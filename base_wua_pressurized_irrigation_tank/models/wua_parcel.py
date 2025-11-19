# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_tank_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_tank')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_tank_table(self):
        # Check if wua gis table already exists
        gis_tank_table_created = \
            self.check_gis_tank_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis tank don't
        if (not gis_tank_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_tank_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_tank
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_tank_gid_seq'::regclass),
                        name character varying(254) NOT NULL
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_tank_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_tank_idx ON public.wua_gis_tank
                    USING gist (geom);
            """)
            self.env.cr.commit()
        self.grant_gis_privileges('wua_gis_tank')

    def create_tank_triggers(self):
        gis_tank_table_created = \
            self.check_gis_tank_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_tank_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_tank data when the
            # wua_gis_tank table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_tank_update_on_wua_tank()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_tank SET
                        with_gis_tank = False
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_tank SET
                        with_gis_tank = True
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis tank is
            # unlinked and other when a gis tank is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_tank_write_trigger ON
                    public.wua_gis_tank;
                DROP TRIGGER IF EXISTS
                    wua_gis_tank_create_unlink_trigger ON
                    public.wua_gis_tank;

                CREATE TRIGGER wua_gis_tank_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_tank FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_tank_update_on_wua_tank();

                CREATE TRIGGER wua_gis_tank_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_tank FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_tank_update_on_wua_tank();
            """)
            self.env.cr.commit()
            # Function that will update the wua_tank data when the
            # wua_tank table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_tank_update_on_wua_tank() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_tank SET with_gis_tank =
                    (SELECT NEW.name IN
                        (SELECT name FROM wua_gis_tank))
                    WHERE name = NEW.name;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the tank is created
            # and other when a gis tank is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_tank_write_trigger ON
                    public.wua_tank;
                DROP TRIGGER IF EXISTS wua_tank_create_trigger ON
                    public.wua_tank;

                CREATE TRIGGER wua_tank_write_trigger
                AFTER UPDATE OF name ON
                public.wua_tank FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_tank_update_on_wua_tank();

                CREATE TRIGGER wua_tank_create_trigger
                AFTER INSERT ON
                public.wua_tank FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_tank_update_on_wua_tank();
            """)
            self.env.cr.commit()

    def set_gis_fields_tank(self):
        gis_tank_ok = self.check_gis_tank_created()
        if (gis_tank_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_tank
                    SET with_gis_tank = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_tank wt1
                    SET with_gis_tank = TRUE
                    FROM public.wua_gis_tank wgt1 WHERE wt1.name = wgt1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_tank_ok = False
        return gis_tank_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_parcels_ok
        #        gis_tank_ok
        #        fail. Only gis_parcels_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_parcels_ok):
        #    return False
        # Call methods
        gis_tank_ok = self.set_gis_fields_tank()
        return gis_parcels_ok and gis_tank_ok
