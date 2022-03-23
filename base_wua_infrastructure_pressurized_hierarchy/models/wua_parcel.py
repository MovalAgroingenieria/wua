# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api,  exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        store=True,
        compute='_compute_waterpipe_id')

    path_wp = fields.Char(
        string="Full name",
        size=255,
        index=True,
        store=True,
        compute="_compute_path_wp")

    waterpipe_01_id = fields.Many2one(
        string="Level 1 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_01_id")

    waterpipe_02_id = fields.Many2one(
        string="Level 2 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_02_id")

    waterpipe_03_id = fields.Many2one(
        string="Level 3 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_03_id")

    waterpipe_04_id = fields.Many2one(
        string="Level 4 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_04_id")

    waterpipe_05_id = fields.Many2one(
        string="Level 5 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_05_id")

    waterpipe_06_id = fields.Many2one(
        string="Level 6 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_06_id")

    waterpipe_07_id = fields.Many2one(
        string="Level 7 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_07_id")

    waterpipe_08_id = fields.Many2one(
        string="Level 8 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_08_id")

    waterpipe_09_id = fields.Many2one(
        string="Level 9 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_09_id")

    waterpipe_10_id = fields.Many2one(
        string="Level 10 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_10_id")

    waterpipe_11_id = fields.Many2one(
        string="Level 11 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_11_id")

    waterpipe_12_id = fields.Many2one(
        string="Level 12 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_12_id")

    waterpipe_13_id = fields.Many2one(
        string="Level 13 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_13_id")

    waterpipe_14_id = fields.Many2one(
        string="Level 14 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_14_id")

    waterpipe_15_id = fields.Many2one(
        string="Level 15 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_15_id")

    waterpipe_16_id = fields.Many2one(
        string="Level 16 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_16_id")

    waterpipe_17_id = fields.Many2one(
        string="Level 17 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_17_id")

    waterpipe_18_id = fields.Many2one(
        string="Level 18 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_18_id")

    waterpipe_19_id = fields.Many2one(
        string="Level 19 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_19_id")

    waterpipe_20_id = fields.Many2one(
        string="Level 20 Water Pipe",
        comodel_name='wua.waterpipe',
        index=True,
        store=True,
        compute="_compute_waterpipe_10_id")

    @api.depends('irrigationpoint_ids', 'irrigationpoint_ids.waterpipe_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            for irrigationpoint in record.irrigationpoint_ids:
                if irrigationpoint.waterpipe_id:
                    waterpipe_id = irrigationpoint.waterpipe_id
                    break
            record.waterpipe_id = waterpipe_id

    @api.depends('waterpipe_id', 'waterpipe_id.path')
    def _compute_path_wp(self):
        for record in self:
            path_wp = ''
            if record.waterpipe_id:
                path_wp = record.waterpipe_id.path
            record.path_wp = path_wp

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_01_id(self):
        for record in self:
            record.waterpipe_01_id = \
                self._get_waterpipe(record, 1)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_02_id(self):
        for record in self:
            record.waterpipe_02_id = \
                self._get_waterpipe(record, 2)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_03_id(self):
        for record in self:
            record.waterpipe_03_id = \
                self._get_waterpipe(record, 3)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_04_id(self):
        for record in self:
            record.waterpipe_04_id = \
                self._get_waterpipe(record, 4)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_05_id(self):
        for record in self:
            record.waterpipe_05_id = \
                self._get_waterpipe(record, 5)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_06_id(self):
        for record in self:
            record.waterpipe_06_id = \
                self._get_waterpipe(record, 6)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_07_id(self):
        for record in self:
            record.waterpipe_07_id = \
                self._get_waterpipe(record, 7)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_08_id(self):
        for record in self:
            record.waterpipe_08_id = \
                self._get_waterpipe(record, 8)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_09_id(self):
        for record in self:
            record.waterpipe_09_id = \
                self._get_waterpipe(record, 9)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_10_id(self):
        for record in self:
            record.waterpipe_10_id = \
                self._get_waterpipe(record, 10)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_11_id(self):
        for record in self:
            record.waterpipe_11_id = \
                self._get_waterpipe(record, 11)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_12_id(self):
        for record in self:
            record.waterpipe_12_id = \
                self._get_waterpipe(record, 12)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_13_id(self):
        for record in self:
            record.waterpipe_13_id = \
                self._get_waterpipe(record, 13)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_14_id(self):
        for record in self:
            record.waterpipe_14_id = \
                self._get_waterpipe(record, 14)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_15_id(self):
        for record in self:
            record.waterpipe_15_id = \
                self._get_waterpipe(record, 15)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_16_id(self):
        for record in self:
            record.waterpipe_16_id = \
                self._get_waterpipe(record, 16)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_17_id(self):
        for record in self:
            record.waterpipe_17_id = \
                self._get_waterpipe(record, 17)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_18_id(self):
        for record in self:
            record.waterpipe_18_id = \
                self._get_waterpipe(record, 18)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_19_id(self):
        for record in self:
            record.waterpipe_19_id = \
                self._get_waterpipe(record, 19)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_20_id(self):
        for record in self:
            record.waterpipe_20_id = \
                self._get_waterpipe(record, 20)

    def _get_waterpipe(self, parcel, level):
        resp = None
        if (parcel.waterpipe_id and parcel.waterpipe_id.level >= level):
            waterpipe = parcel.waterpipe_id
            current_level = waterpipe.level
            while current_level > level:
                waterpipe = waterpipe.waterpipe_id
                current_level = waterpipe.level
            resp = waterpipe
        return resp

    def check_gis_waterpipe_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_waterpipe')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_waterpipe_table(self):
        # Check if wua gis table already exists
        gis_waterpipe_table_created = \
            self.check_gis_waterpipe_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis waterpipe don't
        if (not gis_waterpipe_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_waterpipe_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_waterpipe
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_waterpipe_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(MultiLineString,25830),
                        code bigint,
                        level integer,
                        UNIQUE(code),
                        CONSTRAINT wua_gis_waterpipe_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_waterpipe_idx ON public.wua_gis_waterpipe
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_waterpipe_triggers(self):
        gis_waterpipe_table_created = \
            self.check_gis_waterpipe_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_waterpipe_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_waterpipe data when the
            # wua_gis_waterpipe table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_waterpipe_update_on_wua_waterpipe()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF OLD IS NOT NULL THEN
                    UPDATE public.wua_waterpipe SET
                        with_gis_waterpipe = False
                    WHERE waterpipe_code = OLD.code;
                END IF;
                IF NEW IS NOT NULL THEN
                    UPDATE public.wua_waterpipe SET
                        with_gis_waterpipe = True
                    WHERE waterpipe_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis waterpipe is
            # unlinked and other when a gis waterpipe is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_waterpipe_write_trigger ON
                    public.wua_gis_waterpipe;
                DROP TRIGGER IF EXISTS
                    wua_gis_waterpipe_create_unlink_trigger ON
                    public.wua_gis_waterpipe;

                CREATE TRIGGER wua_gis_waterpipe_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_waterpipe FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_waterpipe_update_on_wua_waterpipe();

                CREATE TRIGGER wua_gis_waterpipe_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_waterpipe FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_waterpipe_update_on_wua_waterpipe();
            """)
            self.env.cr.commit()
            # Function that will update the wua_waterpipe data when the
            # wua_waterpipe table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_waterpipe_update_on_wua_waterpipe() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_waterpipe SET with_gis_waterpipe =
                    (SELECT NEW.waterpipe_code IN
                        (SELECT code FROM wua_gis_waterpipe))
                    WHERE waterpipe_code = NEW.waterpipe_code;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the waterpipe is created
            # and other when a gis waterpipe is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_waterpipe_write_trigger ON
                    public.wua_waterpipe;
                DROP TRIGGER IF EXISTS wua_waterpipe_create_trigger ON
                    public.wua_waterpipe;

                CREATE TRIGGER wua_waterpipe_write_trigger
                AFTER UPDATE OF waterpipe_code ON
                public.wua_waterpipe FOR EACH ROW WHEN
                (OLD.waterpipe_code IS DISTINCT FROM
                    NEW.waterpipe_code)
                EXECUTE PROCEDURE
                    wua_waterpipe_update_on_wua_waterpipe();

                CREATE TRIGGER wua_waterpipe_create_trigger
                AFTER INSERT ON
                public.wua_waterpipe FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_waterpipe_update_on_wua_waterpipe();
            """)
            self.env.cr.commit()

    def create_gis_data(self):
        super(WuaParcel, self).create_gis_data()
        try:
            self.create_wua_gis_waterpipe_table()
            self.create_waterpipe_triggers()
        except Exception:
            pass

    def set_gis_fields_waterpipe(self):
        gis_waterpipe_ok = self.check_gis_waterpipe_created()
        if gis_waterpipe_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_waterpipe
                    SET with_gis_waterpipe = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_waterpipe ww1
                    SET with_gis_waterpipe = TRUE
                    FROM public.wua_gis_waterpipe wgw1 WHERE
                    ww1.waterpipe_code = wgw1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_waterpipe_ok = False
        return gis_waterpipe_ok

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
        gis_waterpipe_ok = self.set_gis_fields_waterpipe()
        return gis_parcels_ok and gis_waterpipe_ok


class WuaParcelIrrigationpoint(models.Model):
    _inherit = 'wua.parcel.irrigationpoint'

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        store=True,
        compute='_compute_waterpipe_id')

    @api.depends('irrigationshed_id', 'irrigationshed_id.waterpipe_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if record.irrigationshed_id.waterpipe_id:
                waterpipe_id = record.irrigationshed_id.waterpipe_id
            record.waterpipe_id = waterpipe_id

    @api.constrains('waterpipe_id')
    def _check_waterpipe_id(self):
        if len(self) == 1:
            irrigationpoint_to_check = self
            if irrigationpoint_to_check.waterpipe_id:
                remaining_irrigationpoint_ids = \
                    self.env['wua.parcel.irrigationpoint'].search(
                        [('parcel_id', '=',
                          irrigationpoint_to_check.parcel_id.id),
                         ('id', '!=', irrigationpoint_to_check.id)])
                if remaining_irrigationpoint_ids:
                    waterpipe_ids = []
                    for irrigationpoint in remaining_irrigationpoint_ids:
                        if irrigationpoint.waterpipe_id:
                            waterpipe_ids.append(
                                irrigationpoint.waterpipe_id.id)
                    if waterpipe_ids:
                        waterpipe_ids = list(set(waterpipe_ids))
                        if len(waterpipe_ids) > 1 or \
                                waterpipe_ids[0] != irrigationpoint_to_check.\
                                waterpipe_id.id:
                            raise exceptions.ValidationError(
                                _('All irrigation points must have the same '
                                  'water-pipe.'))
