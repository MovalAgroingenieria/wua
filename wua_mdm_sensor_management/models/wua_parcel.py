# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    mapped_to_specific_device = fields.Boolean(
        'Associated with a specific device (y/n)',
        compute='_compute_mapped_to_specific_device',
        search='_search_mapped_to_specific_device',
    )

    mapped_to_any_device = fields.Boolean(
        'Associated with any device (y/n)',
        compute='_compute_mapped_to_any_device',
        search='_search_mapped_to_any_device',
    )

    mapped_to_specific_device_as_symbol = fields.Char(
        'Associated with a specific device (y/n) -as symbol-',
        compute='_compute_mapped_to_specific_device_as_symbol',
    )

    deviceparcellink_ids = fields.One2many(
        string='Device Parcel Links',
        comodel_name='mdm.device.parcellink',
        inverse_name='parcel_id',
    )

    @api.multi
    def _compute_mapped_to_specific_device(self):
        mapped_device_id = 0
        if ('mapped_device_id' in self.env.context and
           self.env.context['mapped_device_id']):
            mapped_device_id = self.env.context['mapped_device_id']
        for record in self:
            mapped_to_specific_device = (mapped_device_id == 0)
            if not mapped_to_specific_device:
                sql_statement = ('select id from mdm_device_parcellink '
                                 'where device_id = %s and parcel_id = %s' %
                                 (mapped_device_id, record.id))
                self.env.cr.execute(sql_statement)
                sql_resp = self.env.cr.fetchall()
                if sql_resp:
                    mapped_to_specific_device = True
            record.mapped_to_specific_device = mapped_to_specific_device

    @api.model
    def _search_mapped_to_specific_device(self, operator, value):
        mapped_device_id = 0
        if ('mapped_device_id' in self.env.context and
           self.env.context['mapped_device_id']):
            mapped_device_id = self.env.context['mapped_device_id']
        parcel_ids = []
        operator_of_filter = 'in'
        if operator == '!=':
            operator_of_filter = 'not in'
        if mapped_device_id:
            sql_statement = ('select p.id from wua_parcel p '
                             'inner join mdm_device_parcellink pl '
                             'on p.id = pl.parcel_id '
                             'where pl.device_id = %s' % mapped_device_id)
            self.env.cr.execute(sql_statement)
            sql_resp = self.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    parcel_ids.append(item[0])
        else:
            parcels = self.search([])
            if parcels:
                parcel_ids = parcels.ids
        return [('id', operator_of_filter, parcel_ids)]

    @api.multi
    def _compute_mapped_to_any_device(self):
        for record in self:
            mapped_to_any_device = False
            sql_statement = ('select id from mdm_device_parcellink '
                             'where parcel_id = %s' % record.id)
            self.env.cr.execute(sql_statement)
            sql_resp = self.env.cr.fetchall()
            if sql_resp:
                mapped_to_any_device = True
            record.mapped_to_any_device = mapped_to_any_device

    @api.model
    def _search_mapped_to_any_device(self, operator, value):
        parcel_ids = []
        operator_of_filter = 'in'
        if operator == '!=':
            operator_of_filter = 'not in'
        sql_statement = ('select distinct parcel_id from '
                         'mdm_device_parcellink')
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                parcel_ids.append(item[0])
        return [('id', operator_of_filter, parcel_ids)]

    @api.multi
    def _compute_mapped_to_specific_device_as_symbol(self):
        for record in self:
            mapped_to_specific_device_as_symbol = ''
            if record.mapped_to_specific_device:
                mapped_to_specific_device_as_symbol = '🔗'
            record.mapped_to_specific_device_as_symbol = \
                mapped_to_specific_device_as_symbol

    def check_gis_measurement_device_table_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='mdm_gis_measurement_device')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

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
        gis_measurement_device_ok = self.\
            check_gis_measurement_device_table_created()
        if gis_measurement_device_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.mdm_measurement_device
                    SET with_gis_measurement_device = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.mdm_measurement_device wi1
                    SET with_gis_measurement_device = TRUE
                    FROM public.mdm_gis_measurement_device wgi1 WHERE
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

    @api.model
    def assign_device_to_parcels(self, parcel_ids=None, device_id=0):
        if parcel_ids and device_id:
            parcels = self.browse(parcel_ids)
            device = self.env['mdm.measurement.device'].browse(device_id)
            if parcels and device:
                model_mdm_device_parcellink = self.env['mdm.device.parcellink']
                for parcel in parcels:
                    parcel_id = parcel.id
                    if not model_mdm_device_parcellink.search(
                            [('device_id', '=', device_id),
                             ('parcel_id', '=', parcel_id)]):
                        model_mdm_device_parcellink.create({
                            'device_id': device_id,
                            'parcel_id': parcel_id,
                        })

    @api.model
    def unassign_device_to_parcels(self, parcel_ids=None, device_id=0):
        if parcel_ids and device_id:
            parcels = self.browse(parcel_ids)
            device = self.env['mdm.measurement.device'].browse(device_id)
            if parcels and device:
                model_mdm_device_parcellink = self.env['mdm.device.parcellink']
                for parcel in parcels:
                    parcel_id = parcel.id
                    model_mdm_device_parcellink.search(
                        [('device_id', '=', device_id),
                         ('parcel_id', '=', parcel_id)]).unlink()

    @api.model
    def create(self, vals):
        new_parcel = super(WuaParcel, self).create(vals)
        devices_linked_all_parcels = self.env['mdm.measurement.device'].search(
            [('linked_all_parcels', '=', True)],
        )
        deviceparcellinks = []
        for device in (devices_linked_all_parcels or []):
            deviceparcellinks.append((0, 0, {
                'device_id': device.id,
                'parcel_id': new_parcel.id,
            }))
        if deviceparcellinks:
            new_parcel.write({'deviceparcellink_ids': deviceparcellinks})
        return new_parcel

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_id:
            view = self.env['ir.ui.view'].browse(view_id)
            if view and view.name == 'Parcels (tree view)':
                doc = etree.XML(res['arch'])
                for node in doc.xpath(
                        "//field[@name='mapped_to_specific_device_as_symbol']"):
                    node.set('modifiers', '{"invisible": true}')
                    node.set('modifiers', '{"tree_invisible": true}')
                res['arch'] = etree.tostring(doc)
            if view and view.name == 'wua.parcel.from.device.view.search':
                doc = etree.XML(res['arch'])
                for node in doc.xpath(
                        "//filter[@name='mapped_to_any_device_yes']"):
                    node.set('modifiers', '{"invisible": true}')
                for node in doc.xpath(
                        "//filter[@name='mapped_to_any_device_no']"):
                    node.set('modifiers', '{"invisible": true}')
                res['arch'] = etree.tostring(doc)
            if view and view.name == 'Parcels (search view)':
                doc = etree.XML(res['arch'])
                for node in doc.xpath(
                        "//filter[@name='mapped_to_specific_device_yes']"):
                    node.set('modifiers', '{"invisible": true}')
                for node in doc.xpath(
                        "//filter[@name='mapped_to_specific_device_no']"):
                    node.set('modifiers', '{"invisible": true}')
                res['arch'] = etree.tostring(doc)
        return res
