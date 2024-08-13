# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_measuring_device_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='law_gis_measuring_device')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_law_gis_measuring_device_table(self):
        # Check if law gis table already exists
        gis_measuring_device_table_created = (
            self.check_gis_measuring_device_created())
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis measuring_device don't
        if (not gis_measuring_device_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                        public.law_gis_measuring_device_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.law_gis_measuring_device
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'law_gis_measuring_device_gid_seq'::regclass),
                        name character varying(254) NOT NULL
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point, 25830),
                        CONSTRAINT law_gis_measuring_device_pkey PRIMARY KEY
                            (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                law_gis_measuring_device_idx ON
                    public.law_gis_measuring_device USING
                gist (geom);
            """)
            self.env.cr.commit()

    def create_measuring_device_triggers(self):
        gis_measuring_device_table_created = \
            self.check_gis_measuring_device_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_measuring_device_table_created and
                extension_schema_postgis_created):
            # Function that will update the law_measuring_device data when the
            # law_gis_measuring_device table has some change, (Create, Update
            # or Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    law_gis_measuring_device_update_on_law_measuring_device()
                RETURNS trigger AS
                $BODY$
                BEGIN
               IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.law_measuring_device SET
                        with_gis_measuring_device = False
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.law_measuring_device SET
                        with_gis_measuring_device = True
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis measuring_device is
            # unlinked and other when a gis measuring_device is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS law_gis_measuring_device_write_trigger
                    ON public.law_gis_measuring_device;
                DROP TRIGGER IF EXISTS
                    law_gis_measuring_device_create_unlink_trigger
                    ON public.law_gis_measuring_device;

                CREATE TRIGGER law_gis_measuring_device_write_trigger
                AFTER UPDATE OF name ON
                public.law_gis_measuring_device FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    law_gis_measuring_device_update_on_law_measuring_device();

                CREATE TRIGGER law_gis_measuring_device_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.law_gis_measuring_device FOR EACH ROW
                EXECUTE PROCEDURE
                    law_gis_measuring_device_update_on_law_measuring_device();
            """)
            self.env.cr.commit()
            # Function that will update the law_measuring_device data when the
            # law_measuring_device table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    law_measuring_device_update_on_law_measuring_device()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    NEW.with_gis_measuring_device := (SELECT NEW.name IN
                        (SELECT name FROM law_gis_measuring_device));
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the measuring_device is
            # created and other when a gis measuring_device is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS law_measuring_device_write_trigger ON
                    public.law_measuring_device;
                DROP TRIGGER IF EXISTS law_measuring_device_create_trigger ON
                    public.law_measuring_device;

                CREATE TRIGGER law_measuring_device_write_trigger
                AFTER UPDATE OF name ON
                public.law_measuring_device FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    law_measuring_device_update_on_law_measuring_device();

                CREATE TRIGGER law_measuring_device_create_trigger
                AFTER INSERT ON
                public.law_measuring_device FOR EACH ROW
                EXECUTE PROCEDURE
                    law_measuring_device_update_on_law_measuring_device();
            """)
            self.env.cr.commit()

    # Expand and split original method for measuring_devices
    def set_gis_fields_measuring_device(self):
        gis_measuring_device_ok = self.check_gis_measuring_device_created()
        if gis_measuring_device_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.law_measuring_device
                    SET with_gis_measuring_device = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.law_measuring_device wr1
                    SET with_gis_measuring_device = TRUE
                    FROM public.law_gis_measuring_device wgr1 WHERE
                    wr1.name = wgr1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_measuring_device_ok = False
        return gis_measuring_device_ok

    def set_gis_fields(self):
        gis_measuring_devices_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_measuring_devices_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_measuring_devices_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_measuring_devices_ok):
        #    return False
        # Call methods
        gis_measuring_device_ok = self.set_gis_fields_measuring_device()
        return gis_measuring_devices_ok and gis_measuring_device_ok
