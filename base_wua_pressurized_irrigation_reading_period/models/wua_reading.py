# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

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
        string="Field Reading",
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

    @api.model
    def _prepare_field_reading_values(
        self, watermeter_id, volume, readingperiod_id, watermeter_reader_id,
            product_id, notes='', picture=''):
        vals = {}
        reading_img = None
        if picture:
            reading_img = picture
        vals.update({
            'watermeter_id': watermeter_id,
            'volume': volume,
            'watermeter_reader_id': watermeter_reader_id,
            'notes': notes,
            'reading_time': fields.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            'validated': False,
            'initialization_reading': False,
            'reading_img': reading_img,
        })
        if product_id > 0:
            vals['product_id'] = product_id
        return vals

    @api.model
    def create_field_reading(self, watermeter_id, volume, readingperiod_id,
                             watermeter_reader_id, product_id, notes='',
                             picture='', real_odoo_user_id=False):
        if real_odoo_user_id:
            watermeter_reader_id = real_odoo_user_id
        rp = self.env['wua.readingperiod'].search([('state', '=', 'open')])
        if (not rp):
            raise exceptions.UserError(_(
                'There is no open readingperiod.'))
        vals = self._prepare_field_reading_values(
            watermeter_id, volume, readingperiod_id,
            watermeter_reader_id, product_id, notes, picture)
        vals['readingperiod_id'] = rp.id
        # Removed others readings or negative reading when creating
        # new one
        old_readings = self.sudo().env['wua.reading'].search(
            ['&', ('watermeter_id', '=', watermeter_id),
                ('readingperiod_id', '=', rp.id)])
        if old_readings:
            for old_reading in old_readings:
                self.delete_field_reading(old_reading.id)
        old_negative_readings = self.sudo().env['wua.negative.reading'].search(
            ['&', ('watermeter_id', '=', watermeter_id),
                ('readingperiod_id', '=', rp.id)])
        if old_negative_readings:
            for old_reading in old_negative_readings:
                self.delete_field_negative_reading(old_reading.id)
        # Check if new reading will be positive or negative
        is_negative, negative_volume = self.is_negative_reading(vals)
        try:
            if (is_negative):
                vals['presconsumption_volume'] = negative_volume
                new_reading = self.sudo().env['wua.negative.reading'].create(
                    vals)
            else:
                new_reading = self.sudo().env['wua.reading'].create(vals)
        except Exception as e:
            raise exceptions.UserError(e)
        rpli = self.sudo().env['wua.readingperiod.line.irrigationshed'].\
            search(['&', ('irrigationshed_id', '=', new_reading.watermeter_id.
                    irrigationshed_id.id), ('readingperiod_id', '=', rp.id)])
        if (not rpli):
            raise exceptions.UserError(_(
                'This watermeter does not belong to the open readingperiod.'))
        if (is_negative):
            rpli.write({'negative_reading_ids':
                        [(4, new_reading.id)]})
        else:
            rpli.write({'reading_ids':
                        [(4, new_reading.id)]})
        return new_reading.id

    @api.model
    def delete_field_reading(self, reading_id):
        return self.sudo().env['wua.reading'].browse(reading_id).unlink()

    @api.model
    def delete_field_negative_reading(self, reading_id):
        return self.sudo().env['wua.negative.reading'].browse(reading_id).\
            unlink()
