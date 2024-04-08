# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        index=True,
    )

    def check_gis_flowmeter_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_flowmeter')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_flowmeter_table(self):
        # Check if wua gis table already exists
        gis_flowmeter_table_created = \
            self.check_gis_flowmeter_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis flowmeter don't
        if (not gis_flowmeter_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_flowmeter_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_flowmeter
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_flowmeter_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_flowmeter_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_flowmeter_idx ON public.wua_gis_flowmeter
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_flowmeter_triggers(self):
        gis_flowmeter_table_created = \
            self.check_gis_flowmeter_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_flowmeter_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_flowmeter data when the
            # wua_gis_flowmeter table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_flowmeter_update_on_wua_flowmeter()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_flowmeter SET
                        with_gis_flowmeter = False
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_flowmeter SET
                        with_gis_flowmeter = True
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis flowmeter is
            # unlinked and other when a gis flowmeter is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_flowmeter_write_trigger ON
                    public.wua_gis_flowmeter;
                DROP TRIGGER IF EXISTS
                    wua_gis_flowmeter_create_unlink_trigger ON
                    public.wua_gis_flowmeter;

                CREATE TRIGGER wua_gis_flowmeter_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_flowmeter FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_flowmeter_update_on_wua_flowmeter();

                CREATE TRIGGER wua_gis_flowmeter_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_flowmeter FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_flowmeter_update_on_wua_flowmeter();
            """)
            self.env.cr.commit()
            # Function that will update the wua_flowmeter data when the
            # wua_flowmeter table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_flowmeter_update_on_wua_flowmeter() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_flowmeter SET
                        with_gis_flowmeter = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_flowmeter))
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the flowmeter is created
            # and other when a gis flowmeter is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_flowmeter_write_trigger ON
                    public.wua_flowmeter;
                DROP TRIGGER IF EXISTS wua_flowmeter_create_trigger ON
                    public.wua_flowmeter;

                CREATE TRIGGER wua_flowmeter_write_trigger
                AFTER UPDATE OF name ON
                public.wua_flowmeter FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_flowmeter_update_on_wua_flowmeter();

                CREATE TRIGGER wua_flowmeter_create_trigger
                AFTER INSERT ON
                public.wua_flowmeter FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_flowmeter_update_on_wua_flowmeter();
            """)
            self.env.cr.commit()

    # Expand and split original method for flowmeters and intakes
    def set_gis_fields_flowmeter(self):
        gis_flowmeter_ok = self.check_gis_flowmeter_created()
        if gis_flowmeter_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_flowmeter
                    SET with_gis_flowmeter = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_flowmeter wf1
                    SET with_gis_flowmeter = TRUE
                    FROM public.wua_gis_flowmeter wgf1 WHERE
                    wf1.name = wgf1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_flowmeter_ok = False
        return gis_flowmeter_ok

    def check_gis_intake_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_intake')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_intake_table(self):
        # Check if wua gis table already exists
        gis_intake_table_created = \
            self.check_gis_intake_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis intake don't
        if (not gis_intake_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_intake_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_intake
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_intake_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        code bigint,
                        geom postgis.geometry(Point,25830),
                        UNIQUE(code),
                        CONSTRAINT wua_gis_intake_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_intake_idx ON public.wua_gis_intake
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_intake_triggers(self):
        gis_intake_table_created = \
            self.check_gis_intake_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_intake_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_intake data when the
            # wua_gis_intake table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_intake_update_on_wua_intake()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_intake SET
                        with_gis_intake = False
                    WHERE intake_code = OLD.code;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_intake SET
                        with_gis_intake = True
                    WHERE intake_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis intake is
            # unlinked and other when a gis intake is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_intake_write_trigger ON
                    public.wua_gis_intake;
                DROP TRIGGER IF EXISTS
                    wua_gis_intake_create_unlink_trigger ON
                    public.wua_gis_intake;

                CREATE TRIGGER wua_gis_intake_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_intake FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_intake_update_on_wua_intake();

                CREATE TRIGGER wua_gis_intake_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_intake FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_intake_update_on_wua_intake();
            """)
            self.env.cr.commit()
            # Function that will update the wua_intake data when the
            # wua_intake table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_intake_update_on_wua_intake() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_intake SET
                        with_gis_intake = (SELECT NEW.intake_code IN
                            (SELECT code FROM wua_gis_intake))
                    WHERE intake_code = NEW.intake_code;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the intake is created
            # and other when a gis intake is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_intake_write_trigger ON
                    public.wua_intake;
                DROP TRIGGER IF EXISTS wua_intake_create_trigger ON
                    public.wua_intake;

                CREATE TRIGGER wua_intake_write_trigger
                AFTER UPDATE OF intake_code ON
                public.wua_intake FOR EACH ROW WHEN
                (OLD.intake_code IS DISTINCT FROM NEW.intake_code)
                EXECUTE PROCEDURE
                    wua_intake_update_on_wua_intake();

                CREATE TRIGGER wua_intake_create_trigger
                AFTER INSERT ON
                public.wua_intake FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_intake_update_on_wua_intake();
            """)
            self.env.cr.commit()

    def set_gis_fields_intake(self):
        gis_intake_ok = self.check_gis_intake_created()
        if gis_intake_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_intake
                    SET with_gis_intake = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_intake wi1
                    SET with_gis_intake = TRUE
                    FROM public.wua_gis_intake wgi1 WHERE
                    wi1.intake_code = wgi1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_intake_ok = False
        return gis_intake_ok

    # Filteringstation
    def check_gis_filteringstation_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_filteringstation')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_filteringstation_table(self):
        # Check if wua gis table already exists
        gis_filteringstation_table_created = \
            self.check_gis_filteringstation_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis filteringstation don't
        if (not gis_filteringstation_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_filteringstation_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_filteringstation
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_filteringstation_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_filteringstation_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_filteringstation_idx ON public.wua_gis_filteringstation
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_filteringstation_triggers(self):
        gis_filteringstation_table_created = \
            self.check_gis_filteringstation_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_filteringstation_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_filteringstation data when the
            # wua_gis_filteringstation table has some change, (Create,
            # Update or Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_filteringstation_update_on_wua_filteringstation()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_filteringstation SET
                        with_gis_filteringstation = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_filteringstation SET
                        with_gis_filteringstation = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis filteringstation is
            # unlinked and other when a gis filteringstation is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_filteringstation_write_trigger
                    ON public.wua_gis_filteringstation;
                DROP TRIGGER IF EXISTS
                    wua_gis_filteringstation_create_unlink_trigger ON
                    public.wua_gis_filteringstation;

                CREATE TRIGGER wua_gis_filteringstation_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_filteringstation FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_filteringstation_update_on_wua_filteringstation();

                CREATE TRIGGER wua_gis_filteringstation_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_filteringstation FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_filteringstation_update_on_wua_filteringstation();
            """)
            self.env.cr.commit()
            # Function that will update the wua_filteringstation data when the
            # wua_filteringstation table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_filteringstation_update_on_wua_filteringstation()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_filteringstation SET
                        with_gis_filteringstation = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_filteringstation)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_filteringstation WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_filteringstation WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the filteringstation is
            # created and other when a gis filteringstation is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_filteringstation_write_trigger ON
                    public.wua_filteringstation;
                DROP TRIGGER IF EXISTS wua_filteringstation_create_trigger ON
                    public.wua_filteringstation;

                CREATE TRIGGER wua_filteringstation_write_trigger
                AFTER UPDATE OF name ON
                public.wua_filteringstation FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_filteringstation_update_on_wua_filteringstation();

                CREATE TRIGGER wua_filteringstation_create_trigger
                AFTER INSERT ON
                public.wua_filteringstation FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_filteringstation_update_on_wua_filteringstation();
            """)
            self.env.cr.commit()

    def set_gis_fields_filteringstation(self):
        gis_filteringstation_ok = self.check_gis_filteringstation_created()
        if (gis_filteringstation_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_filteringstation
                    SET with_gis_filteringstation = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_filteringstation wi1
                    SET with_gis_filteringstation = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_draiangevalve wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_filteringstation_ok = False
        return gis_filteringstation_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_parcels_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_parcels_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_parcels_ok):
        #    return False
        # Call methods
        gis_flowmeter_ok = self.set_gis_fields_flowmeter()
        gis_intake_ok = self.set_gis_fields_intake()
        # filteringstation GIS
        gis_filteringstation_ok = self.set_gis_fields_filteringstation()
        return gis_parcels_ok and gis_flowmeter_ok and gis_intake_ok and \
            gis_filteringstation_ok
