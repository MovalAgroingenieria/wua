# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_powerline_table_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_powerline')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_powerline_table(self):
        # Check if the GIS table already exists
        gis_table_created = self.check_gis_powerline_table_created()
        # Check if PostGIS extension and schema are created
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_powerline_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_powerline (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_powerline_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(MultiLineString,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_powerline_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_powerline_idx ON public.wua_gis_powerline
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_powerline_triggers(self):
        gis_table_created = self.check_gis_powerline_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_powerline_update_on_wua_powerline()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_powerline SET
                            with_gis_powerline = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_powerline SET
                            with_gis_powerline = True
                        WHERE name = NEW.name;
                    END IF;
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            # Triggers on the GIS table
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_powerline_write_trigger ON
                    public.wua_gis_powerline;
                DROP TRIGGER IF EXISTS
                    wua_gis_powerline_create_unlink_trigger ON
                    public.wua_gis_powerline;

                CREATE TRIGGER wua_gis_powerline_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_powerline FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_powerline_update_on_wua_powerline();

                CREATE TRIGGER wua_gis_powerline_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_powerline FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_powerline_update_on_wua_powerline();
            """)
            self.env.cr.commit()

            # Function to sync from wua_powerline to GIS state
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_powerline_update_on_wua_powerline()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_powerline SET
                        with_gis_powerline = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_powerline
                            )
                        )
                    WHERE name = NEW.name;
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            # Triggers on wua_powerline
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_powerline_write_trigger ON
                    public.wua_powerline;
                DROP TRIGGER IF EXISTS wua_powerline_create_trigger ON
                    public.wua_powerline;

                CREATE TRIGGER wua_powerline_write_trigger
                AFTER UPDATE OF name ON
                public.wua_powerline FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_powerline_update_on_wua_powerline();

                CREATE TRIGGER wua_powerline_create_trigger
                AFTER INSERT ON
                public.wua_powerline FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_powerline_update_on_wua_powerline();
            """)
            self.env.cr.commit()

    def set_gis_fields_powerline(self):
        gis_powerline_ok = self.check_gis_powerline_table_created()
        if gis_powerline_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_powerline
                    SET with_gis_powerline = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_powerline wp1
                    SET with_gis_powerline = TRUE
                    FROM public.wua_gis_powerline wgp1
                    WHERE wp1.name = wgp1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_powerline_ok = False
        return gis_powerline_ok

    def check_gis_powerlinesupport_table_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT * FROM information_schema.tables
                WHERE table_name = 'wua_gis_powerlinesupport'
            )
        """)
        return self.env.cr.fetchone()[0]

    def create_wua_gis_powerlinesupport_table(self):
        gis_table_created = self.check_gis_powerlinesupport_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_powerlinesupport_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_powerlinesupport (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_powerlinesupport_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(Point,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_powerlinesupport_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_powerlinesupport_idx ON
                    public.wua_gis_powerlinesupport
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_powerlinesupport_triggers(self):
        gis_table_created = self.check_gis_powerlinesupport_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_powerlinesupport_update_on_wua_powerlinesupport()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_powerlinesupport SET
                            with_gis_powerlinesupport = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_powerlinesupport SET
                            with_gis_powerlinesupport = True
                        WHERE name = NEW.name;
                    END IF;
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_powerlinesupport_write_trigger
                ON public.wua_gis_powerlinesupport;
                DROP TRIGGER IF EXISTS
                    wua_gis_powerlinesupport_create_unlink_trigger ON
                    public.wua_gis_powerlinesupport;

                CREATE TRIGGER wua_gis_powerlinesupport_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_powerlinesupport FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_powerlinesupport_update_on_wua_powerlinesupport();

                CREATE TRIGGER wua_gis_powerlinesupport_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_powerlinesupport FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_powerlinesupport_update_on_wua_powerlinesupport();
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_powerlinesupport_update_on_wua_powerlinesupport()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_powerlinesupport SET
                        with_gis_powerlinesupport = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_powerlinesupport
                            )
                        )
                    WHERE name = NEW.name;
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_powerlinesupport_write_trigger ON
                    public.wua_powerlinesupport;
                DROP TRIGGER IF EXISTS wua_powerlinesupport_create_trigger ON
                    public.wua_powerlinesupport;

                CREATE TRIGGER wua_powerlinesupport_write_trigger
                AFTER UPDATE OF name ON
                public.wua_powerlinesupport FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_powerlinesupport_update_on_wua_powerlinesupport();

                CREATE TRIGGER wua_powerlinesupport_create_trigger
                AFTER INSERT ON
                public.wua_powerlinesupport FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_powerlinesupport_update_on_wua_powerlinesupport();
            """)
            self.env.cr.commit()

    def set_gis_fields_powerlinesupport(self):
        gis_ok = self.check_gis_powerlinesupport_table_created()
        if gis_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_powerlinesupport
                    SET with_gis_powerlinesupport = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_powerlinesupport wpls
                    SET with_gis_powerlinesupport = TRUE
                    FROM public.wua_gis_powerlinesupport wgpls
                    WHERE wpls.name = wgpls.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_ok = False
        return gis_ok

    def check_gis_processingcentre_table_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT * FROM information_schema.tables
                WHERE table_name = 'wua_gis_processingcentre'
            )
        """)
        return self.env.cr.fetchone()[0]

    def create_wua_gis_processingcentre_table(self):
        gis_table_created = self.check_gis_processingcentre_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_processingcentre_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_processingcentre (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_processingcentre_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(Point,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_processingcentre_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_processingcentre_idx ON
                    public.wua_gis_processingcentre
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_processingcentre_triggers(self):
        gis_table_created = self.check_gis_processingcentre_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_processingcentre_update_on_wua_processingcentre()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_processingcentre SET
                            with_gis_processingcentre = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_processingcentre SET
                            with_gis_processingcentre = True
                        WHERE name = NEW.name;
                    END IF;
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_processingcentre_write_trigger
                ON public.wua_gis_processingcentre;
                DROP TRIGGER IF EXISTS
                    wua_gis_processingcentre_create_unlink_trigger ON
                    public.wua_gis_processingcentre;

                CREATE TRIGGER wua_gis_processingcentre_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_processingcentre FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_processingcentre_update_on_wua_processingcentre();

                CREATE TRIGGER wua_gis_processingcentre_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_processingcentre FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_processingcentre_update_on_wua_processingcentre();
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_processingcentre_update_on_wua_processingcentre()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_processingcentre SET
                        with_gis_processingcentre = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_processingcentre
                            )
                        )
                    WHERE name = NEW.name;
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_processingcentre_write_trigger ON
                    public.wua_processingcentre;
                DROP TRIGGER IF EXISTS wua_processingcentre_create_trigger ON
                    public.wua_processingcentre;

                CREATE TRIGGER wua_processingcentre_write_trigger
                AFTER UPDATE OF name ON
                public.wua_processingcentre FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_processingcentre_update_on_wua_processingcentre();

                CREATE TRIGGER wua_processingcentre_create_trigger
                AFTER INSERT ON
                public.wua_processingcentre FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_processingcentre_update_on_wua_processingcentre();
            """)
            self.env.cr.commit()

    def check_extension_and_schema_postgis_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension
                WHERE extname = 'postgis'
            );
        """)
        postgis_ext = self.env.cr.fetchone()[0]

        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name = 'public'
            );
        """)
        public_schema = self.env.cr.fetchone()[0]

        return postgis_ext and public_schema

    def set_gis_fields_processingcentre(self):
        gis_processingcentre_ok = self.check_gis_drainagevalve_created()
        if (gis_processingcentre_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_processingcentre
                    SET with_gis_processingcentre = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_processingcentre wi1
                    SET with_gis_processingcentre = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_processingcentre wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_processingcentre_ok = False
        return gis_processingcentre_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # Processing centre GIS
        gis_processingcentre_ok = self.set_gis_fields_processingcentre()
        # Power line support GIS
        gis_powerlinesupport_ok = self.set_gis_fields_powerlinesupport()
        # Power line GIS
        gis_powerline_ok = self.set_gis_fields_powerline()
        return gis_parcels_ok and gis_processingcentre_ok and \
            gis_powerlinesupport_ok and gis_powerline_ok
