# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_reservoir_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_reservoir')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_reservoir_table(self):
        # Check if wua gis table already exists
        gis_reservoir_table_created = self.check_gis_reservoir_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis reservoir don't
        if (not gis_reservoir_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS public.wua_gis_reservoir_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_reservoir
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_reservoir_gid_seq'::regclass),
                        name character varying(254) NOT NULL
                            COLLATE pg_catalog."default",
                        code bigint,
                        geom postgis.geometry(MultiPolygon,25830),
                        UNIQUE(code),
                        CONSTRAINT wua_gis_reservoir_pkey PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_reservoir_idx ON public.wua_gis_reservoir USING
                gist (geom);
            """)
            self.env.cr.commit()

    def create_reservoir_triggers(self):
        gis_reservoir_table_created = self.check_gis_reservoir_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_reservoir_table_created and extension_schema_postgis_created):
            # Function that will update the wua_reservoir data when the
            # wua_gis_reservoir table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_reservoir_update_on_wua_reservoir() RETURNS trigger
                AS
                $BODY$
                BEGIN
                IF OLD IS NOT NULL THEN
                    UPDATE public.wua_reservoir SET with_gis_reservoir = False
                        WHERE reservoir_code = OLD.code;
                END IF;
                IF NEW IS NOT NULL THEN
                    UPDATE public.wua_reservoir SET with_gis_reservoir = True
                        WHERE reservoir_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis reservoir is unlinked
            # and other when a gis reservoir is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_reservoir_write_trigger ON
                    public.wua_gis_reservoir;
                DROP TRIGGER IF EXISTS wua_gis_reservoir_create_unlink_trigger
                    ON public.wua_gis_reservoir;

                CREATE TRIGGER wua_gis_reservoir_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_reservoir FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE wua_gis_reservoir_update_on_wua_reservoir();

                CREATE TRIGGER wua_gis_reservoir_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_reservoir FOR EACH ROW
                EXECUTE PROCEDURE wua_gis_reservoir_update_on_wua_reservoir();
            """)
            self.env.cr.commit()
            # Function that will update the wua_reservoir data when the
            # wua_reservoir table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_reservoir_update_on_wua_reservoir() RETURNS trigger AS
                $BODY$
                BEGIN
                    NEW.with_gis_reservoir := (SELECT NEW.reservoir_code IN
                        (SELECT code FROM wua_gis_reservoir));
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the reservoir is created and
            # other when a gis reservoir is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_reservoir_write_trigger ON
                    public.wua_reservoir;
                DROP TRIGGER IF EXISTS wua_reservoir_create_trigger ON
                    public.wua_reservoir;

                CREATE TRIGGER wua_reservoir_write_trigger
                AFTER UPDATE OF reservoir_code ON
                public.wua_reservoir FOR EACH ROW WHEN
                (OLD.reservoir_code IS DISTINCT FROM NEW.reservoir_code)
                EXECUTE PROCEDURE wua_reservoir_update_on_wua_reservoir();

                CREATE TRIGGER wua_reservoir_create_trigger
                AFTER INSERT ON
                public.wua_reservoir FOR EACH ROW
                EXECUTE PROCEDURE wua_reservoir_update_on_wua_reservoir();
            """)
            self.env.cr.commit()

    def create_gis_data(self):
        super(WuaParcel, self).create_gis_data()
        try:
            self.create_wua_gis_reservoir_table()
            self.create_reservoir_triggers()
        except Exception:
            pass

    # Expand and split original method for reservoirs
    def set_gis_fields_reservoir(self):
        gis_reservoir_ok = self.check_gis_reservoir_created()
        if gis_reservoir_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_reservoir
                    SET with_gis_reservoir = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_reservoir wr1
                    SET with_gis_reservoir = TRUE
                    FROM public.wua_gis_reservoir wgr1 WHERE
                    wr1.reservoir_code = wgr1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_reservoir_ok = False
        return gis_reservoir_ok

    def set_gis_fields(self):
        gis_reservoirs_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_reservoirs_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_reservoirs_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_reservoirs_ok):
        #    return False
        # Call methods
        gis_reservoir_ok = self.set_gis_fields_reservoir()
        return gis_reservoirs_ok and gis_reservoir_ok
