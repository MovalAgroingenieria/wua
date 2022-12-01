# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def check_gis_pressuresensor_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_pressuresensor')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_pressuresensor_table(self):
        # Check if wua gis table already exists
        gis_pressuresensor_table_created = \
            self.check_gis_pressuresensor_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis pressuresensor don't
        if (not gis_pressuresensor_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_pressuresensor_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_pressuresensor
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_pressuresensor_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_pressuresensor_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_pressuresensor_idx ON public.wua_gis_pressuresensor
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_pressuresensor_triggers(self):
        gis_pressuresensor_table_created = \
            self.check_gis_pressuresensor_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_pressuresensor_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_pressuresensor data when the
            # wua_gis_pressuresensor table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_pressuresensor_update_on_wua_pressuresensor()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_pressuresensor SET
                        with_gis_pressuresensor = False
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_pressuresensor SET
                        with_gis_pressuresensor = True
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis pressuresensor is
            # unlinked and other when a gis pressuresensor is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_pressuresensor_write_trigger ON
                    public.wua_gis_pressuresensor;
                DROP TRIGGER IF EXISTS
                    wua_gis_pressuresensor_create_unlink_trigger ON
                    public.wua_gis_pressuresensor;

                CREATE TRIGGER wua_gis_pressuresensor_write_trigger
                AFTER UPDATE OF name ON
                public.wua_gis_pressuresensor FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_pressuresensor_update_on_wua_pressuresensor();

                CREATE TRIGGER wua_gis_pressuresensor_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_pressuresensor FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_pressuresensor_update_on_wua_pressuresensor();
            """)
            self.env.cr.commit()
            # Function that will update the wua_pressuresensor data when the
            # wua_pressuresensor table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_pressuresensor_update_on_wua_pressuresensor() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_pressuresensor SET
                        with_gis_pressuresensor = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_pressuresensor))
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the pressuresensor is created
            # and other when a gis pressuresensor is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_pressuresensor_write_trigger ON
                    public.wua_pressuresensor;
                DROP TRIGGER IF EXISTS wua_pressuresensor_create_trigger ON
                    public.wua_pressuresensor;

                CREATE TRIGGER wua_pressuresensor_write_trigger
                AFTER UPDATE OF name ON
                public.wua_pressuresensor FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_pressuresensor_update_on_wua_pressuresensor();

                CREATE TRIGGER wua_pressuresensor_create_trigger
                AFTER INSERT ON
                public.wua_pressuresensor FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_pressuresensor_update_on_wua_pressuresensor();
            """)
            self.env.cr.commit()

    def create_gis_data(self):
        super(WuaParcel, self).create_gis_data()
        try:
            self.create_wua_gis_pressuresensor_table()
            self.create_pressuresensor_triggers()
        except Exception:
            pass


class WuaParcelIrrigationpointWC(models.Model):
    _inherit = 'wua.parcel.irrigationpointwc'

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        compute='_compute_watermeter_id')

    @api.multi
    def _compute_watermeter_id(self):
        for record in self:
            record.watermeter_id = record.waterconnection_id.watermeter_id
