# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    SIZE_PATH = 255

    irrigationditch_direct_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    path = fields.Char(
        string="Irrigation Ditch Full name",
        size=SIZE_PATH,
        index=True,
        store=True,
        compute="_compute_path")

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

    @api.depends('irrigationditch_id', 'irrigationditch_id.path')
    def _compute_path(self):
        for record in self:
            path = ''
            if record.irrigationditch_id:
                path = record.irrigationditch_id.path
            record.path = path

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
