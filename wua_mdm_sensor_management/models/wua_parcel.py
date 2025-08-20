# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_measurement_device_table_created(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT * FROM information_schema.tables
                WHERE table_name = 'mdm_gis_measurement_device'
            )
        """)
        return self.env.cr.fetchone()[0]

    def create_mdm_gis_measurement_device_table(self):
        gis_table_created = self.check_gis_measurement_device_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()
        if not gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.mdm_gis_measurement_device_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.mdm_gis_measurement_device (
                    gid integer NOT NULL DEFAULT nextval(
                        'mdm_gis_measurement_device_gid_seq'::regclass),
                    name character varying(254)
                        COLLATE pg_catalog."default",
                    geom postgis.geometry(Point,25830),
                    UNIQUE(name),
                    CONSTRAINT mdm_gis_measurement_device_pkey
                        PRIMARY KEY (gid)
                );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                    mdm_gis_measurement_device_idx ON
                    public.mdm_gis_measurement_device
                    USING gist (geom);
            """)
            self.env.cr.commit()
        self.grant_gis_privileges('mdm_gis_measurement_device')

    def create_measurement_device_triggers(self):
        gis_table_created = self.check_gis_measurement_device_table_created()
        postgis_ready = self.check_extension_and_schema_postgis_created()

        if gis_table_created and postgis_ready:
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    mdm_gis_measurement_device_update_on_mdm_measurement_device()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                        UPDATE public.mdm_measurement_device SET
                            with_gis_measurement_device = False
                        WHERE name = OLD.name;
                    END IF;
                    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                        UPDATE public.mdm_measurement_device SET
                            with_gis_measurement_device = True
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
                DROP TRIGGER IF EXISTS mdm_gis_measurement_device_write_trigger
                ON public.mdm_gis_measurement_device;
                DROP TRIGGER IF EXISTS
                    mdm_gis_measurement_device_create_unlink_trigger ON
                    public.mdm_gis_measurement_device;

                CREATE TRIGGER mdm_gis_measurement_device_write_trigger
                AFTER UPDATE OF name ON
                public.mdm_gis_measurement_device FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    mdm_gis_measurement_device_update_on_mdm_measurement_device();

                CREATE TRIGGER mdm_gis_measurement_device_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.mdm_gis_measurement_device FOR EACH ROW
                EXECUTE PROCEDURE
                    mdm_gis_measurement_device_update_on_mdm_measurement_device();
            """)
            self.env.cr.commit()

            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    mdm_measurement_device_update_on_mdm_measurement_device()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE public.mdm_measurement_device SET
                        with_gis_measurement_device = (
                            SELECT NEW.name IN (
                                SELECT name FROM mdm_gis_measurement_device
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
                DROP TRIGGER IF EXISTS mdm_measurement_device_write_trigger ON
                    public.mdm_measurement_device;
                DROP TRIGGER IF EXISTS mdm_measurement_device_create_trigger ON
                    public.mdm_measurement_device;

                CREATE TRIGGER mdm_measurement_device_write_trigger
                AFTER UPDATE OF name ON
                public.mdm_measurement_device FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    mdm_measurement_device_update_on_mdm_measurement_device();

                CREATE TRIGGER mdm_measurement_device_create_trigger
                AFTER INSERT ON
                public.mdm_measurement_device FOR EACH ROW
                EXECUTE PROCEDURE
                    mdm_measurement_device_update_on_mdm_measurement_device();
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

    def set_gis_fields_measurement_device(self):
        gis_measurement_device_ok = self.check_gis_drainagevalve_created()
        if (gis_measurement_device_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.mdm_measurement_device
                    SET with_gis_measurement_device = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.mdm_measurement_device wi1
                    SET with_gis_measurement_device = TRUE

                    FROM public.mdm_measurement_device wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_measurement_device_ok = False
        return gis_measurement_device_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        gis_measurement_device_ok = self.set_gis_fields_measurement_device()
        return gis_parcels_ok and gis_measurement_device_ok
