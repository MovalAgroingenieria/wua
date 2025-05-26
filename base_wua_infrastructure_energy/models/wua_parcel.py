# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_power_line_table_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_power_line')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_power_line_table(self):
        # Check if the GIS table already exists
        gis_table_created = self.check_gis_power_line_table_created()
        # Check if PostGIS extension and schema are created
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_power_line_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_power_line (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_power_line_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(MultiLineString,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_power_line_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_power_line_idx ON public.wua_gis_power_line
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_power_line_triggers(self):
        gis_table_created = self.check_gis_power_line_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_power_line_update_on_wua_power_line()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_power_line SET
                            with_gis_power_line = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_power_line SET
                            with_gis_power_line = True
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
                DROP TRIGGER IF EXISTS wua_gis_power_line_write_trigger ON
                    public.wua_gis_power_line;
                DROP TRIGGER IF EXISTS
                    wua_gis_power_line_create_unlink_trigger ON
                    public.wua_gis_power_line;

                CREATE TRIGGER wua_gis_power_line_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_power_line FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_power_line_update_on_wua_power_line();

                CREATE TRIGGER wua_gis_power_line_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_power_line FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_power_line_update_on_wua_power_line();
            """)
            self.env.cr.commit()

            # Function to sync from wua_power_line to GIS state
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_power_line_update_on_wua_power_line()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_power_line SET
                        with_gis_power_line = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_power_line
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

            # Triggers on wua_power_line
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_power_line_write_trigger ON
                    public.wua_power_line;
                DROP TRIGGER IF EXISTS wua_power_line_create_trigger ON
                    public.wua_power_line;

                CREATE TRIGGER wua_power_line_write_trigger
                AFTER UPDATE OF name ON
                public.wua_power_line FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_power_line_update_on_wua_power_line();

                CREATE TRIGGER wua_power_line_create_trigger
                AFTER INSERT ON
                public.wua_power_line FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_power_line_update_on_wua_power_line();
            """)
            self.env.cr.commit()

    def set_gis_fields_power_line(self):
        gis_power_line_ok = self.check_gis_power_line_table_created()
        if gis_power_line_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_power_line
                    SET with_gis_power_line = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_power_line wp1
                    SET with_gis_power_line = TRUE
                    FROM public.wua_gis_power_line wgp1
                    WHERE wp1.name = wgp1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_power_line_ok = False
        return gis_power_line_ok

    def check_gis_power_line_support_table_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT * FROM information_schema.tables
                WHERE table_name = 'wua_gis_power_line_support'
            )
        """)
        return self.env.cr.fetchone()[0]

    def create_wua_gis_power_line_support_table(self):
        gis_table_created = self.check_gis_power_line_support_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_power_line_support_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_power_line_support (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_power_line_support_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(Point,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_power_line_support_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_power_line_support_idx ON
                    public.wua_gis_power_line_support
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_power_line_support_triggers(self):
        gis_table_created = self.check_gis_power_line_support_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_power_line_support_update_on_wua_power_line_support()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_power_line_support SET
                            with_gis_power_line_support = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_power_line_support SET
                            with_gis_power_line_support = True
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
                DROP TRIGGER IF EXISTS wua_gis_power_line_support_write_trigger ON
                    public.wua_gis_power_line_support;
                DROP TRIGGER IF EXISTS
                    wua_gis_power_line_support_create_unlink_trigger ON
                    public.wua_gis_power_line_support;

                CREATE TRIGGER wua_gis_power_line_support_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_power_line_support FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_power_line_support_update_on_wua_power_line_support();

                CREATE TRIGGER wua_gis_power_line_support_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_power_line_support FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_power_line_support_update_on_wua_power_line_support();
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_power_line_support_update_on_wua_power_line_support()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_power_line_support SET
                        with_gis_power_line_support = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_power_line_support
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
                DROP TRIGGER IF EXISTS wua_power_line_support_write_trigger ON
                    public.wua_power_line_support;
                DROP TRIGGER IF EXISTS wua_power_line_support_create_trigger ON
                    public.wua_power_line_support;

                CREATE TRIGGER wua_power_line_support_write_trigger
                AFTER UPDATE OF name ON
                public.wua_power_line_support FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_power_line_support_update_on_wua_power_line_support();

                CREATE TRIGGER wua_power_line_support_create_trigger
                AFTER INSERT ON
                public.wua_power_line_support FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_power_line_support_update_on_wua_power_line_support();
            """)
            self.env.cr.commit()

    def set_gis_fields_power_line_support(self):
        gis_ok = self.check_gis_power_line_support_table_created()
        if gis_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_power_line_support
                    SET with_gis_power_line_support = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_power_line_support wpls
                    SET with_gis_power_line_support = TRUE
                    FROM public.wua_gis_power_line_support wgpls
                    WHERE wpls.name = wgpls.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_ok = False
        return gis_ok

    def check_gis_processing_centre_table_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT * FROM information_schema.tables
                WHERE table_name = 'wua_gis_processing_centre'
            )
        """)
        return self.env.cr.fetchone()[0]


    def create_wua_gis_processing_centre_table(self):
        gis_table_created = self.check_gis_processing_centre_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_processing_centre_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_processing_centre (
                    gid integer NOT NULL DEFAULT nextval(
                        'wua_gis_processing_centre_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(Point,25830),
                    UNIQUE(name),
                    CONSTRAINT wua_gis_processing_centre_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    wua_gis_processing_centre_idx ON
                    public.wua_gis_processing_centre
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_processing_centre_triggers(self):
        gis_table_created = self.check_gis_processing_centre_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_processing_centre_update_on_wua_processing_centre()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.wua_processing_centre SET
                            with_wua_processing_centre = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.wua_processing_centre SET
                            with_wua_processing_centre = True
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
                DROP TRIGGER IF EXISTS wua_gis_processing_centre_write_trigger ON
                    public.wua_gis_processing_centre;
                DROP TRIGGER IF EXISTS
                    wua_gis_processing_centre_create_unlink_trigger ON
                    public.wua_gis_processing_centre;

                CREATE TRIGGER wua_gis_processing_centre_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_processing_centre FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_processing_centre_update_on_wua_processing_centre();

                CREATE TRIGGER wua_gis_processing_centre_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_processing_centre FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_processing_centre_update_on_wua_processing_centre();
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_processing_centre_update_on_wua_processing_centre()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_processing_centre SET
                        with_wua_processing_centre = (
                            SELECT NEW.name IN (
                                SELECT name FROM wua_gis_processing_centre
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
                DROP TRIGGER IF EXISTS wua_processing_centre_write_trigger ON
                    public.wua_processing_centre;
                DROP TRIGGER IF EXISTS wua_processing_centre_create_trigger ON
                    public.wua_processing_centre;

                CREATE TRIGGER wua_processing_centre_write_trigger
                AFTER UPDATE OF name ON
                public.wua_processing_centre FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_processing_centre_update_on_wua_processing_centre();

                CREATE TRIGGER wua_processing_centre_create_trigger
                AFTER INSERT ON
                public.wua_processing_centre FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_processing_centre_update_on_wua_processing_centre();
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
