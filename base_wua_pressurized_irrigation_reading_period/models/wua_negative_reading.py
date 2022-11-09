# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaNegativeReading(models.Model):
    _inherit = 'wua.negative.reading'

    readingperiod_id = fields.Many2one(
        string="Reading Period",
        index=True,
        comodel_name='wua.readingperiod',
        ondelete='restrict',
        readonly=True)

    watermeter_reader_id = fields.Many2one(
        string="Water-Meter Reader",
        index=True,
        comodel_name="res.users",
        ondelete='restrict',
        readonly=True)

    is_field_reading = fields.Boolean(
        string="From field",
        compute='_compute_is_field_reading',
        store=True)

    readingperiodlineirrigationshed_id = fields.Many2one(
        comodel_name='wua.readingperiod.line.irrigationshed',
        index=True,
        readonly=True,
        ondelete='restrict')

    reading_img = fields.Binary(
        string="Reading Image",
        readonly=True,
        attachment=True)

    @api.depends('readingperiod_id')
    def _compute_is_field_reading(self):
        for record in self:
            is_field_reading = False
            if (record.readingperiod_id):
                is_field_reading = True
            record.is_field_reading = is_field_reading

    @api.constrains('is_field_reading')
    def _check_is_field_reading(self):
        if (len(self) == 1 and (self.is_field_reading) and
                (not self.readingperiod_id or not self.watermeter_reader_id)):
            raise exceptions.ValidationError(_(
                'Field readings must have a watermeter reader and reading '
                'period.'))

    @api.constrains('watermeter_reader_id')
    def _check_watermeter_reader_id(self):
        if (len(self) == 1 and (self.watermeter_reader_id) and
                (not self.watermeter_reader_id.has_group(
                    'base_wua_pressurized_irrigation_reading_period.'
                    'group_wua_watermeter_reader'))):
            raise exceptions.ValidationError(_(
                'This User don\'t belongs to watermeter reader group.'))
