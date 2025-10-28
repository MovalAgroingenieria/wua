# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions

class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    _my_mapped_device_id = 0

    mapped_to_specific_device = fields.Boolean(
        'Associated with a specific device (y/n)',
        compute='_compute_mapped_to_specific_device',
        search='_search_mapped_to_specific_device',
    )

    device_parcellink_ids = fields.One2many(
        string='Device Parcel Links',
        comodel_name='mdm.device.parcellink',
        inverse_name='parcel_id',
    )

    @api.multi
    def _compute_mapped_to_specific_device(self):
        mapped_device_id = self.env.context.get('mapped_device_id', None)
        parcel_ids = tuple(self.ids)
        if len(parcel_ids) == 1:
            parcel_ids = parcel_ids + (0,)

        # Case 1: mapped_device_id == 0 → all parcels are mapped
        if mapped_device_id == 0:
            for record in self:
                record.mapped_to_specific_device = True
            return

        # Case 2: No context → check if the parcel is linked to *specific* device
        if mapped_device_id is None:
            self.env.cr.execute("""
                SELECT DISTINCT parcel_id
                FROM mdm_device_parcellink
                WHERE parcel_id IN %s
            """, (parcel_ids,))
            linked_parcel_ids = {row[0] for row in self.env.cr.fetchall()}
            for record in self:
                record.mapped_to_specific_device = record.id in linked_parcel_ids
            return

        # Case 3: Specific device ID in context
        self.env.cr.execute("""
            SELECT parcel_id
            FROM mdm_device_parcellink
            WHERE device_id = %s
            AND parcel_id IN %s
        """, (mapped_device_id, parcel_ids))
        linked_parcel_ids = {row[0] for row in self.env.cr.fetchall()}

        for record in self:
            record.mapped_to_specific_device = record.id in linked_parcel_ids

    @api.model
    def _search_mapped_to_specific_device(self, operator, value):
        mapped_device_id = self.env.context.get('mapped_device_id', None)

        # Case 1: mapped_device_id == 0 → all parcels are linked
        # (device with linked_all_parcels=True)
        if mapped_device_id == 0:
            searching_for_linked = (operator == '=' and value) or (operator == '!=' and not value)
            if searching_for_linked:
                # Return all parcels
                return []
            else:
                # Return no parcels
                return [('id', '=', False)]
        # Case 2: No context → check if parcel is linked to any specific device
        if mapped_device_id is None:
            self.env.cr.execute("""
                SELECT DISTINCT parcel_id
                FROM mdm_device_parcellink
            """)
            linked_parcel_ids = [row[0] for row in self.env.cr.fetchall()]

            searching_for_linked = (operator == '=' and value) or (operator == '!=' and not value)
            if searching_for_linked:
                return [('id', 'in', linked_parcel_ids)] if linked_parcel_ids else [('id', '=', False)]
            else:
                return [('id', 'not in', linked_parcel_ids)] if linked_parcel_ids else []

        # Case 3: Specific device ID in context
        self.env.cr.execute("""
            SELECT p.id
            FROM wua_parcel p
            INNER JOIN mdm_device_parcellink pl
                ON p.id = pl.parcel_id
            WHERE pl.device_id = %s
        """, (mapped_device_id,))

        linked_parcel_ids = [row[0] for row in self.env.cr.fetchall()]

        searching_for_linked = (operator == '=' and value) or (operator == '!=' and not value)
        if searching_for_linked:
            return [('id', 'in', linked_parcel_ids)] if linked_parcel_ids else [('id', '=', False)]
        else:
            return [('id', 'not in', linked_parcel_ids)] if linked_parcel_ids else []


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

    @api.multi
    def assign_device(self, limit=0):
        device_id = self._my_mapped_device_id
        if device_id:
            model_mdm_device_parcellink = self.env['mdm.device.parcellink']
            for record in self:
                parcel_id = record.id
                if not model_mdm_device_parcellink.search(
                        [('device_id', '=', device_id),
                         ('parcel_id', '=', parcel_id)]):
                    model_mdm_device_parcellink.create({
                        'device_id': device_id,
                        'parcel_id': parcel_id,
                    })

    def unassign_device(self, limit=0):
        device_id = self._my_mapped_device_id
        if device_id:
            model_mdm_device_parcellink = self.env['mdm.device.parcellink']
            for record in self:
                parcel_id = record.id
                model_mdm_device_parcellink.search(
                    [('device_id', '=', device_id),
                     ('parcel_id', '=', parcel_id)]).unlink()

    @api.model
    def create(self, vals):
        new_parcel = super(WuaParcel, self).create(vals)
        devices_linked_all_parcels = self.env['mdm.measurement.device'].search(
            [('linked_all_parcels', '=', True)]
        )
        deviceparcellinks = []
        for device in (devices_linked_all_parcels or []):
            deviceparcellinks.append((0, 0, {
                'device_id': device.id,
                'parcel_id': new_parcel.id,
            }))
        if deviceparcellinks:
            new_parcel.write({'device_parcellink_ids': deviceparcellinks})
        return new_parcel
