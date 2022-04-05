# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_pumpgroup_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_pumpgroup')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_pumpgroup_table(self):
        # Check if wua gis table already exists
        gis_pumpgroup_table_created = \
            self.check_gis_pumpgroup_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis pumpgroup don't
        if (not gis_pumpgroup_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_pumpgroup_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_pumpgroup
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_pumpgroup_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        code bigint,
                        geom postgis.geometry(Point,25830),
                        UNIQUE(code),
                        CONSTRAINT wua_gis_pumpgroup_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_pumpgroup_idx ON public.wua_gis_pumpgroup
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_pumpgroup_triggers(self):
        gis_pumpgroup_table_created = \
            self.check_gis_pumpgroup_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_pumpgroup_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_pumpgroup data when the
            # wua_gis_pumpgroup table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_pumpgroup_update_on_wua_pumpgroup()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_pumpgroup SET
                        with_gis_pumpgroup = False
                    WHERE pumpgroup_code = OLD.code;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_pumpgroup SET
                        with_gis_pumpgroup = True
                    WHERE pumpgroup_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis pumpgroup is
            # unlinked and other when a gis pumpgroup is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_pumpgroup_write_trigger ON
                    public.wua_gis_pumpgroup;
                DROP TRIGGER IF EXISTS
                    wua_gis_pumpgroup_create_unlink_trigger ON
                    public.wua_gis_pumpgroup;

                CREATE TRIGGER wua_gis_pumpgroup_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_pumpgroup FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_pumpgroup_update_on_wua_pumpgroup();

                CREATE TRIGGER wua_gis_pumpgroup_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_pumpgroup FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_pumpgroup_update_on_wua_pumpgroup();
            """)
            self.env.cr.commit()
            # Function that will update the wua_pumpgroup data when the
            # wua_pumpgroup table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_pumpgroup_update_on_wua_pumpgroup() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_pumpgroup SET
                        with_gis_pumpgroup = (SELECT NEW.pumpgroup_code IN
                            (SELECT code FROM wua_gis_pumpgroup))
                    WHERE pumpgroup_code = NEW.pumpgroup_code;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the pumpgroup is created
            # and other when a gis pumpgroup is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_pumpgroup_write_trigger ON
                    public.wua_pumpgroup;
                DROP TRIGGER IF EXISTS wua_pumpgroup_create_trigger ON
                    public.wua_pumpgroup;

                CREATE TRIGGER wua_pumpgroup_write_trigger
                AFTER UPDATE OF pumpgroup_code ON
                public.wua_pumpgroup FOR EACH ROW WHEN
                (OLD.pumpgroup_code IS DISTINCT FROM NEW.pumpgroup_code)
                EXECUTE PROCEDURE
                    wua_pumpgroup_update_on_wua_pumpgroup();

                CREATE TRIGGER wua_pumpgroup_create_trigger
                AFTER INSERT ON
                public.wua_pumpgroup FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_pumpgroup_update_on_wua_pumpgroup();
            """)
            self.env.cr.commit()

    def check_gis_photovoltaicplant_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_photovoltaicplant')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_photovoltaicplant_table(self):
        # Check if wua gis table already exists
        gis_photovoltaicplant_table_created = \
            self.check_gis_photovoltaicplant_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis photovoltaicplant don't
        if (not gis_photovoltaicplant_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_photovoltaicplant_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_photovoltaicplant
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_photovoltaicplant_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        code bigint,
                        geom postgis.geometry(MultiPolygon,25830),
                        UNIQUE(code),
                        CONSTRAINT wua_gis_photovoltaicplant_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_photovoltaicplant_idx ON
                public.wua_gis_photovoltaicplant USING gist (geom);
            """)
            self.env.cr.commit()

    def create_photovoltaicplant_triggers(self):
        gis_photovoltaicplant_table_created = \
            self.check_gis_photovoltaicplant_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_photovoltaicplant_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_photovoltaicplant data when the
            # wua_gis_photovoltaicplant table has some change, (Create, Update
            # or Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_photovoltaicplant_update_on_wua_photovoltaicplant()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_photovoltaicplant SET
                        with_gis_photovoltaicplant = False
                    WHERE photovoltaicplant_code = OLD.code;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_photovoltaicplant SET
                        with_gis_photovoltaicplant = True
                    WHERE photovoltaicplant_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis photovoltaicplant is
            # unlinked and other when a gis photovoltaicplant is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_photovoltaicplant_write_trigger
                    ON public.wua_gis_photovoltaicplant;
                DROP TRIGGER IF EXISTS
                    wua_gis_photovoltaicplant_create_unlink_trigger ON
                    public.wua_gis_photovoltaicplant;

                CREATE TRIGGER wua_gis_photovoltaicplant_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_photovoltaicplant FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_photovoltaicplant_update_on_wua_photovoltaicplant();

                CREATE TRIGGER wua_gis_photovoltaicplant_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_photovoltaicplant FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_photovoltaicplant_update_on_wua_photovoltaicplant();
            """)
            self.env.cr.commit()
            # Function that will update the wua_photovoltaicplant data when the
            # wua_photovoltaicplant table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_photovoltaicplant_update_on_wua_photovoltaicplant()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_photovoltaicplant SET
                        with_gis_photovoltaicplant = (SELECT
                            NEW.photovoltaicplant_code IN
                            (SELECT code FROM wua_gis_photovoltaicplant))
                    WHERE photovoltaicplant_code = NEW.photovoltaicplant_code;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the photovoltaicplant is
            # created and other when a gis photovoltaicplant is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_photovoltaicplant_write_trigger ON
                    public.wua_photovoltaicplant;
                DROP TRIGGER IF EXISTS wua_photovoltaicplant_create_trigger ON
                    public.wua_photovoltaicplant;

                CREATE TRIGGER wua_photovoltaicplant_write_trigger
                AFTER UPDATE OF photovoltaicplant_code ON
                public.wua_photovoltaicplant FOR EACH ROW WHEN
                (OLD.photovoltaicplant_code IS DISTINCT FROM
                 NEW.photovoltaicplant_code)
                EXECUTE PROCEDURE
                    wua_photovoltaicplant_update_on_wua_photovoltaicplant();

                CREATE TRIGGER wua_photovoltaicplant_create_trigger
                AFTER INSERT ON
                public.wua_photovoltaicplant FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_photovoltaicplant_update_on_wua_photovoltaicplant();
            """)
            self.env.cr.commit()

    def set_gis_fields_pumpgroup(self):
        gis_pumpgroup_ok = self.check_gis_pumpgroup_created()
        if gis_pumpgroup_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_pumpgroup
                    SET with_gis_pumpgroup = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_pumpgroup wp1
                    SET with_gis_pumpgroup = TRUE
                    FROM public.wua_gis_pumpgroup wgp1 WHERE
                    wp1.pumpgroup_code = wgp1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_pumpgroup_ok = False
        return gis_pumpgroup_ok

    def set_gis_fields_photovoltaicplant(self):
        gis_photovoltaicplant_ok = self.check_gis_photovoltaicplant_created()
        if gis_photovoltaicplant_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_photovoltaicplant
                    SET with_gis_photovoltaicplant = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_photovoltaicplant wp1
                    SET with_gis_photovoltaicplant = TRUE
                    FROM public.wua_gis_photovoltaicplant wgp1 WHERE
                    wp1.photovoltaicplant_code = wgp1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_photovoltaicplant_ok = False
        return gis_photovoltaicplant_ok

    def create_gis_data(self):
        try:
            self.create_wua_gis_pumpgroup_table()
            self.create_pumpgroup_triggers()
            self.create_wua_gis_photovoltaicplant_table()
            self.create_photovoltaicplant_triggers()
        except Exception:
            pass

    # Expand original method
    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_parcels_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_parcels_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_parcels_ok):
        #    return False
        # Check pumpgrouops
        gis_pumpgroup_ok = self.set_gis_fields_pumpgroup()
        # Check photovoltaicplants
        gis_photovoltaicplant_ok = self.set_gis_fields_photovoltaicplant()
        return gis_parcels_ok and gis_pumpgroup_ok and gis_photovoltaicplant_ok
