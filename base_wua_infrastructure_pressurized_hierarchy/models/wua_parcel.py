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
        compute="_compute_path")

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

    @api.depends('irrigationpoint_ids', 'irrigationpoint_ids.waterpipe_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            for irrigationpoint in record.irrigationpoint_ids:
                if irrigationpoint.waterpipe_id:
                    waterpipe_id = irrigationpoint.waterpipe_id
                    break
            record.waterpipe_id = waterpipe_id

    @api.depends('waterpipe_id')
    def _compute_path(self):
        for record in self:
            path = ''
            if record.waterpipe_id:
                path = record.waterpipe_id.path
            record.path = path

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_01_id(self):
        for record in self:
            record.waterpipe_01_id = \
                self.get_waterpipe(record, 1)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_02_id(self):
        for record in self:
            record.waterpipe_02_id = \
                self.get_waterpipe(record, 2)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_03_id(self):
        for record in self:
            record.waterpipe_03_id = \
                self.get_waterpipe(record, 3)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_04_id(self):
        for record in self:
            record.waterpipe_04_id = \
                self.get_waterpipe(record, 4)

    @api.depends('waterpipe_id', 'waterpipe_id.level')
    def _compute_waterpipe_05_id(self):
        for record in self:
            record.waterpipe_05_id = \
                self.get_waterpipe(record, 5)

    def get_waterpipe(self, parcel, level):
        resp = None
        if (parcel.waterpipe_id and parcel.waterpipe_id.level >= level):
            waterpipe = parcel.waterpipe_id
            current_level = waterpipe.level
            while current_level > level:
                waterpipe = waterpipe.irrigationditch_id
                current_level = waterpipe.level
            resp = waterpipe
        return resp


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
