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

    irrigationditch_08_id = fields.Many2one(
        string="Level 8 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_08")

    irrigationditch_09_id = fields.Many2one(
        string="Level 9 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_09")

    irrigationditch_10_id = fields.Many2one(
        string="Level 10 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_10")

    irrigationditch_11_id = fields.Many2one(
        string="Level 11 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_11")

    irrigationditch_12_id = fields.Many2one(
        string="Level 12 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_12")

    irrigationditch_13_id = fields.Many2one(
        string="Level 13 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_13")

    irrigationditch_14_id = fields.Many2one(
        string="Level 14 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_14")

    irrigationditch_15_id = fields.Many2one(
        string="Level 15 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_15")

    irrigationditch_16_id = fields.Many2one(
        string="Level 16 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_16")

    irrigationditch_17_id = fields.Many2one(
        string="Level 17 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_17")

    irrigationditch_18_id = fields.Many2one(
        string="Level 18 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_18")

    irrigationditch_19_id = fields.Many2one(
        string="Level 19 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_19")

    irrigationditch_20_id = fields.Many2one(
        string="Level 20 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_20")

    irrigationditch_21_id = fields.Many2one(
        string="Level 21 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_21")

    irrigationditch_22_id = fields.Many2one(
        string="Level 22 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_22")

    irrigationditch_23_id = fields.Many2one(
        string="Level 23 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_23")

    irrigationditch_24_id = fields.Many2one(
        string="Level 24 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_24")

    irrigationditch_25_id = fields.Many2one(
        string="Level 25 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_25")

    irrigationditch_26_id = fields.Many2one(
        string="Level 26 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_26")

    irrigationditch_27_id = fields.Many2one(
        string="Level 27 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_27")

    irrigationditch_28_id = fields.Many2one(
        string="Level 28 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_28")

    irrigationditch_29_id = fields.Many2one(
        string="Level 29 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_29")

    irrigationditch_30_id = fields.Many2one(
        string="Level 30 Irrigation Ditch",
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute="_compute_irrigationditch_id_30")

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

    drainageditch_08_id = fields.Many2one(
        string="Level 8 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_08")

    drainageditch_09_id = fields.Many2one(
        string="Level 9 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_09")

    drainageditch_10_id = fields.Many2one(
        string="Level 10 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_10")

    drainageditch_11_id = fields.Many2one(
        string="Level 11 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_11")

    drainageditch_12_id = fields.Many2one(
        string="Level 12 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_12")

    drainageditch_13_id = fields.Many2one(
        string="Level 13 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_13")

    drainageditch_14_id = fields.Many2one(
        string="Level 14 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_14")

    drainageditch_15_id = fields.Many2one(
        string="Level 15 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_15")

    drainageditch_16_id = fields.Many2one(
        string="Level 16 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_16")

    drainageditch_17_id = fields.Many2one(
        string="Level 17 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_17")

    drainageditch_18_id = fields.Many2one(
        string="Level 18 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_18")

    drainageditch_19_id = fields.Many2one(
        string="Level 19 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_19")

    drainageditch_20_id = fields.Many2one(
        string="Level 20 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_20")

    drainageditch_21_id = fields.Many2one(
        string="Level 21 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_21")

    drainageditch_22_id = fields.Many2one(
        string="Level 22 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_22")

    drainageditch_23_id = fields.Many2one(
        string="Level 23 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_23")

    drainageditch_24_id = fields.Many2one(
        string="Level 24 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_24")

    drainageditch_25_id = fields.Many2one(
        string="Level 25 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_25")

    drainageditch_26_id = fields.Many2one(
        string="Level 26 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_26")

    drainageditch_27_id = fields.Many2one(
        string="Level 27 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_27")

    drainageditch_28_id = fields.Many2one(
        string="Level 28 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_28")

    drainageditch_29_id = fields.Many2one(
        string="Level 29 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_29")

    drainageditch_30_id = fields.Many2one(
        string="Level 30 Drainage Ditch",
        comodel_name='wua.drainageditch',
        index=True,
        store=True,
        compute="_compute_drainageditch_id_30")

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
                record.irrigationditch_direct_id

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

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_08(self):
        for record in self:
            record.irrigationditch_08_id = \
                self.get_irrigationditch(record, 8)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_09(self):
        for record in self:
            record.irrigationditch_09_id = \
                self.get_irrigationditch(record, 9)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_10(self):
        for record in self:
            record.irrigationditch_10_id = \
                self.get_irrigationditch(record, 10)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_11(self):
        for record in self:
            record.irrigationditch_11_id = \
                self.get_irrigationditch(record, 11)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_12(self):
        for record in self:
            record.irrigationditch_12_id = \
                self.get_irrigationditch(record, 12)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_13(self):
        for record in self:
            record.irrigationditch_13_id = \
                self.get_irrigationditch(record, 13)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_14(self):
        for record in self:
            record.irrigationditch_14_id = \
                self.get_irrigationditch(record, 14)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_15(self):
        for record in self:
            record.irrigationditch_15_id = \
                self.get_irrigationditch(record, 15)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_16(self):
        for record in self:
            record.irrigationditch_16_id = \
                self.get_irrigationditch(record, 16)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_17(self):
        for record in self:
            record.irrigationditch_17_id = \
                self.get_irrigationditch(record, 17)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_18(self):
        for record in self:
            record.irrigationditch_18_id = \
                self.get_irrigationditch(record, 18)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_19(self):
        for record in self:
            record.irrigationditch_19_id = \
                self.get_irrigationditch(record, 19)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_20(self):
        for record in self:
            record.irrigationditch_20_id = \
                self.get_irrigationditch(record, 20)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_21(self):
        for record in self:
            record.irrigationditch_21_id = \
                self.get_irrigationditch(record, 21)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_22(self):
        for record in self:
            record.irrigationditch_22_id = \
                self.get_irrigationditch(record, 22)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_23(self):
        for record in self:
            record.irrigationditch_23_id = \
                self.get_irrigationditch(record, 23)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_24(self):
        for record in self:
            record.irrigationditch_24_id = \
                self.get_irrigationditch(record, 24)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_25(self):
        for record in self:
            record.irrigationditch_25_id = \
                self.get_irrigationditch(record, 25)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_26(self):
        for record in self:
            record.irrigationditch_26_id = \
                self.get_irrigationditch(record, 26)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_27(self):
        for record in self:
            record.irrigationditch_27_id = \
                self.get_irrigationditch(record, 27)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_28(self):
        for record in self:
            record.irrigationditch_28_id = \
                self.get_irrigationditch(record, 28)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_29(self):
        for record in self:
            record.irrigationditch_29_id = \
                self.get_irrigationditch(record, 29)

    @api.depends('irrigationditch_id', 'irrigationditch_id.level')
    def _compute_irrigationditch_id_30(self):
        for record in self:
            record.irrigationditch_30_id = \
                self.get_irrigationditch(record, 30)

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

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_08(self):
        for record in self:
            record.drainageditch_08_id = \
                self.get_drainageditch(record, 8)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_09(self):
        for record in self:
            record.drainageditch_09_id = \
                self.get_drainageditch(record, 9)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_10(self):
        for record in self:
            record.drainageditch_10_id = \
                self.get_drainageditch(record, 10)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_11(self):
        for record in self:
            record.drainageditch_11_id = \
                self.get_drainageditch(record, 11)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_12(self):
        for record in self:
            record.drainageditch_12_id = \
                self.get_drainageditch(record, 12)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_13(self):
        for record in self:
            record.drainageditch_13_id = \
                self.get_drainageditch(record, 13)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_14(self):
        for record in self:
            record.drainageditch_14_id = \
                self.get_drainageditch(record, 14)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_15(self):
        for record in self:
            record.drainageditch_15_id = \
                self.get_drainageditch(record, 15)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_16(self):
        for record in self:
            record.drainageditch_16_id = \
                self.get_drainageditch(record, 16)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_17(self):
        for record in self:
            record.drainageditch_17_id = \
                self.get_drainageditch(record, 17)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_18(self):
        for record in self:
            record.drainageditch_18_id = \
                self.get_drainageditch(record, 18)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_19(self):
        for record in self:
            record.drainageditch_19_id = \
                self.get_drainageditch(record, 19)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_20(self):
        for record in self:
            record.drainageditch_20_id = \
                self.get_drainageditch(record, 20)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_21(self):
        for record in self:
            record.drainageditch_21_id = \
                self.get_drainageditch(record, 21)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_22(self):
        for record in self:
            record.drainageditch_22_id = \
                self.get_drainageditch(record, 22)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_23(self):
        for record in self:
            record.drainageditch_23_id = \
                self.get_drainageditch(record, 23)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_24(self):
        for record in self:
            record.drainageditch_24_id = \
                self.get_drainageditch(record, 24)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_25(self):
        for record in self:
            record.drainageditch_25_id = \
                self.get_drainageditch(record, 25)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_26(self):
        for record in self:
            record.drainageditch_26_id = \
                self.get_drainageditch(record, 26)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_27(self):
        for record in self:
            record.drainageditch_27_id = \
                self.get_drainageditch(record, 27)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_28(self):
        for record in self:
            record.drainageditch_28_id = \
                self.get_drainageditch(record, 28)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_29(self):
        for record in self:
            record.drainageditch_29_id = \
                self.get_drainageditch(record, 29)

    @api.depends('drainageditch_id', 'drainageditch_id.level')
    def _compute_drainageditch_id_30(self):
        for record in self:
            record.drainageditch_30_id = \
                self.get_drainageditch(record, 30)

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

    def check_gis_drainageditch_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_drainageditch')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_drainageditch_table(self):
        # Check if wua gis table already exists
        gis_drainageditch_table_created = \
            self.check_gis_drainageditch_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis drainageditch don't
        if (not gis_drainageditch_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_drainageditch_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_drainageditch
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_drainageditch_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(MultiLineString,25830),
                        code bigint,
                        level integer,
                        UNIQUE(code),
                        CONSTRAINT wua_gis_drainageditch_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_drainageditch_idx ON public.wua_gis_drainageditch
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_drainageditch_triggers(self):
        gis_drainageditch_table_created = \
            self.check_gis_drainageditch_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_drainageditch_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_drainageditch data when the
            # wua_gis_drainageditch table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_drainageditch_update_on_wua_drainageditch()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_drainageditch SET
                        with_gis_drainageditch = False
                    WHERE drainageditch_code = OLD.code;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_drainageditch SET
                        with_gis_drainageditch = True
                    WHERE drainageditch_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis drainageditch is
            # unlinked and other when a gis drainageditch is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_drainageditch_write_trigger ON
                    public.wua_gis_drainageditch;
                DROP TRIGGER IF EXISTS
                    wua_gis_drainageditch_create_unlink_trigger ON
                    public.wua_gis_drainageditch;

                CREATE TRIGGER wua_gis_drainageditch_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_drainageditch FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_drainageditch_update_on_wua_drainageditch();

                CREATE TRIGGER wua_gis_drainageditch_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_drainageditch FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_drainageditch_update_on_wua_drainageditch();
            """)
            self.env.cr.commit()
            # Function that will update the wua_drainageditch data when the
            # wua_drainageditch table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_drainageditch_update_on_wua_drainageditch() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_drainageditch SET with_gis_drainageditch =
                    (SELECT NEW.drainageditch_code IN
                        (SELECT code FROM wua_gis_drainageditch))
                    WHERE drainageditch_code = NEW.drainageditch_code;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the drainageditch is created
            # and other when a gis drainageditch is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_drainageditch_write_trigger ON
                    public.wua_drainageditch;
                DROP TRIGGER IF EXISTS wua_drainageditch_create_trigger ON
                    public.wua_drainageditch;

                CREATE TRIGGER wua_drainageditch_write_trigger
                AFTER UPDATE OF drainageditch_code ON
                public.wua_drainageditch FOR EACH ROW WHEN
                (OLD.drainageditch_code IS DISTINCT FROM
                    NEW.drainageditch_code)
                EXECUTE PROCEDURE
                    wua_drainageditch_update_on_wua_drainageditch();

                CREATE TRIGGER wua_drainageditch_create_trigger
                AFTER INSERT ON
                public.wua_drainageditch FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_drainageditch_update_on_wua_drainageditch();
            """)
            self.env.cr.commit()

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
        gis_drainageditch_ok = self.check_gis_drainageditch_created()
        if gis_drainageditch_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_drainageditch
                    SET with_gis_drainageditch = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_drainageditch wd1
                    SET with_gis_drainageditch = TRUE
                    FROM public.wua_gis_drainageditch wgd1 WHERE
                    wd1.drainageditch_code = wgd1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_drainageditch_ok = False
        return gis_parcels_ok and gis_drainageditch_ok
