# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    SIZE_PATH = 255

    irrigationditch_direct_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    drainageditch_id = fields.Many2one(
        string='Drainage Ditch',
        comodel_name='wua.drainageditch',
        index=True,
        ondelete='restrict')

    path = fields.Char(
        string="Irrigation Ditch Full name",
        size=SIZE_PATH,
        index=True,
        store=True,
        compute="_compute_path")

    drain_path = fields.Char(
        string="Drainage Ditch Full name",
        size=SIZE_PATH,
        index=True,
        store=True,
        compute="_compute_drain_path")

    irrigationditch_01_id = fields.Many2one(
        string="Level 1 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_01")

    irrigationditch_02_id = fields.Many2one(
        string="Level 2 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_02")

    irrigationditch_03_id = fields.Many2one(
        comodel_name='wua.irrigationditch',
        string="Level 3 Irrigation Ditch",
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_03")

    irrigationditch_04_id = fields.Many2one(
        string="Level 4 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_04")

    irrigationditch_05_id = fields.Many2one(
        string="Level 5 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_05")

    irrigationditch_06_id = fields.Many2one(
        string="Level 6 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_06")

    irrigationditch_07_id = fields.Many2one(
        string="Level 7 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_07")

    drainageditch_01_id = fields.Many2one(
        string="Level 1 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_01")

    drainageditch_02_id = fields.Many2one(
        string="Level 2 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_02")

    drainageditch_03_id = fields.Many2one(
        string="Level 3 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_03")

    drainageditch_04_id = fields.Many2one(
        string="Level 4 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_04")

    drainageditch_05_id = fields.Many2one(
        string="Level 5 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_05")

    drainageditch_06_id = fields.Many2one(
        string="Level 6 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_06")

    drainageditch_07_id = fields.Many2one(
        string="Level 7 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_07")

    @api.depends('irrigationditch_id', 'irrigationditch_id.path')
    def _compute_path(self):
        for record in self:
            path = ''
            if record.irrigationditch_id:
                path = record.irrigationditch_id.path
            record.path = path

    @api.depends('drainageditch_id', 'drainageditch_id.path')
    def _compute_drain_path(self):
        for record in self:
            drain_path = ''
            if record.drainageditch_id:
                drain_path = record.drainageditch_id.path
            record.drain_path = drain_path

    @api.depends('irrigationditch_direct_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            record.irrigationditch_id = \
                self.irrigationditch_direct_id

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_01(self):
        for record in self:
            record.irrigationditch_01_id = \
                self.get_irrigationditch(record, 1)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_02(self):
        for record in self:
            record.irrigationditch_02_id = \
                self.get_irrigationditch(record, 2)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_03(self):
        for record in self:
            record.irrigationditch_03_id = \
                self.get_irrigationditch(record, 3)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_04(self):
        for record in self:
            record.irrigationditch_04_id = \
                self.get_irrigationditch(record, 4)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_05(self):
        for record in self:
            record.irrigationditch_05_id = \
                self.get_irrigationditch(record, 5)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_06(self):
        for record in self:
            record.irrigationditch_06_id = \
                self.get_irrigationditch(record, 6)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_07(self):
        for record in self:
            record.irrigationditch_07_id = \
                self.get_irrigationditch(record, 7)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_01(self):
        for record in self:
            record.drainageditch_01_id = \
                self.get_drainageditch(record, 1)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_02(self):
        for record in self:
            record.drainageditch_02_id = \
                self.get_drainageditch(record, 2)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_03(self):
        for record in self:
            record.drainageditch_03_id = \
                self.get_drainageditch(record, 3)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_04(self):
        for record in self:
            record.drainageditch_04_id = \
                self.get_drainageditch(record, 4)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_05(self):
        for record in self:
            record.drainageditch_05_id = \
                self.get_drainageditch(record, 5)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_06(self):
        for record in self:
            record.drainageditch_06_id = \
                self.get_drainageditch(record, 6)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_07(self):
        for record in self:
            record.drainageditch_07_id = \
                self.get_drainageditch(record, 7)

    @api.depends('irrigationpoint_ids', 'irrigationditch_id')
    def _compute_hydraulic_infrastructure_type(self):
        for record in self:
            hydraulic_infrastructure_type = 0
            for irrigation_point in record.irrigationpoint_ids:
                if hydraulic_infrastructure_type == 0:
                    if irrigation_point.type == 'WC':
                        hydraulic_infrastructure_type = 1
                    if irrigation_point.type == 'IG':
                        hydraulic_infrastructure_type = 2
                if (hydraulic_infrastructure_type == 1 and
                   irrigation_point.type == 'IG'):
                    hydraulic_infrastructure_type = 3
                if (hydraulic_infrastructure_type == 2 and
                   irrigation_point.type == 'WC'):
                    hydraulic_infrastructure_type = 3
                if hydraulic_infrastructure_type == 3:
                    break
            if record.irrigationditch_id:
                if hydraulic_infrastructure_type == 1:
                    hydraulic_infrastructure_type = 3
                else:
                    hydraulic_infrastructure_type = 2
            record.hydraulic_infrastructure_type = \
                hydraulic_infrastructure_type

    def get_irrigationditch(self, parcel, level):
        resp = None
        if (parcel.irrigationditch_id and
           parcel.irrigationditch_id.level >= level):
            irrigationditch = parcel.irrigationditch_id
            current_level = irrigationditch.level
            while current_level > level:
                irrigationditch = irrigationditch.irrigationditch_id
                current_level = irrigationditch.level
            resp = irrigationditch
        return resp

    def get_drainageditch(self, parcel, level):
        resp = None
        if (parcel.drainageditch_id and
           parcel.drainageditch_id.level >= level):
            drainageditch = parcel.drainageditch_id
            current_level = drainageditch.level
            while current_level > level:
                drainageditch = drainageditch.drainageditch_id
                current_level = drainageditch.level
            resp = drainageditch
        return resp

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
        gis_drainageditch_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_drainageditch')
            """)
        if self.env.cr.fetchone()[0]:
            gis_drainageditch_ok = True
        if gis_drainageditch_ok:
            self.env.cr.execute("""
                SELECT code, geom FROM public.wua_gis_drainageditch
                """)
            gis_drainageditchs = self.env.cr.fetchall()
            if gis_drainageditchs:
                drainageditchs = self.env['wua.drainageditch'].search([])
                number_of_gis_drainageditchs = len(gis_drainageditchs)
                number_of_drainageditchs = len(drainageditchs)
                self.env.cr.execute("""
                    UPDATE public.wua_drainageditch
                    SET with_gis_drainageditch = FALSE
                    """)
                for gis_drainageditch in gis_drainageditchs:
                    code = gis_drainageditch[0]
                    filtered_drainageditchs = \
                        drainageditchs.filtered(
                            lambda x: x.drainageditch_code == code)
                    if len(filtered_drainageditchs) == 1:
                        drainageditch = filtered_drainageditchs[0]
                        drainageditch.write({
                            'with_gis_drainageditch': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-Drainageditchs: ' +
                             str(number_of_drainageditchs))
                _logger.info('Number of GIS-Drainageditchs : ' +
                             str(number_of_gis_drainageditchs))
        return gis_parcels_ok and gis_drainageditch_ok
