# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaWaterpipeflowreading(models.Model):
    _inherit = 'wua.waterpipeflowreading'

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
    def create_field_reading(self, flowmeter_id, volume, instant_flow,
                             watermeter_reader_id, notes='', picture='',
                             real_odoo_user_id=False):
        if real_odoo_user_id:
            watermeter_reader_id = real_odoo_user_id
        readingperiod_model = self.sudo().env['wua.readingperiod']
        readingperiodflowmeterline_model = \
            self.sudo().env['wua.readingperiod.flowmeterline']
        waterpipeflowreading_model = self.sudo().\
            env['wua.waterpipeflowreading']
        readingperiod = readingperiod_model.search(
            [('state', '=', 'open')])
        waterpipe = self.sudo().env['wua.flowmeter'].browse(flowmeter_id).\
            waterpipe_id
        if ((not readingperiod) or (not waterpipe)):
            raise exceptions.UserError(_(
                'There is no open reading period, or no connected waterpipe.'))
        reading_img = None
        if (picture):
            reading_img = picture
        vals = {
            'flowmeter_id': flowmeter_id,
            'reading_time': fields.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            'volume': volume,
            'instant_flow': instant_flow,
            'initialization_reading': False,
            'waterpipe_id': waterpipe.id,
            'notes': notes,
            'readingperiod_id': readingperiod.id,
            'watermeter_reader_id': watermeter_reader_id,
            'reading_img': reading_img
            }
        # Removed others readings or negative reading when creating
        # new one
        old_waterpipeflowreading = waterpipeflowreading_model.search(
            [('readingperiod_id', '=', readingperiod.id),
             ('flowmeter_id', '=', flowmeter_id)])
        if old_waterpipeflowreading:
            old_waterpipeflowreading.unlink()
        old_negative_flowreading = self.sudo().\
            env['wua.negative.flowreading'].search(
                ['&', ('flowmeter_id', '=', flowmeter_id),
                 ('readingperiod_id', '=', readingperiod.id)])
        if old_negative_flowreading:
            old_negative_flowreading.unlink()
        # Check if new reading will be positive or negative
        is_negative, negative_volume = self.is_negative_waterpipeflowreading(
            vals)
        try:
            if (is_negative):
                vals['consumption_volume'] = negative_volume
                new_waterpipeflowreading = self.sudo().\
                    env['wua.negative.flowreading'].create(vals)
            else:
                new_waterpipeflowreading = waterpipeflowreading_model.\
                    create(vals)
        except Exception as e:
            raise exceptions.UserError(e)
        readingperiodflowmeterline = readingperiodflowmeterline_model.search(
            [('readingperiod_id', '=', readingperiod.id),
             ('flowmeter_id', '=', flowmeter_id)])
        if not readingperiodflowmeterline:
            raise exceptions.UserError(_(
                'This flowmeter does not belong to the open reading period.'))
        if (is_negative):
            readingperiodflowmeterline.write(
                {'negative_flowreading_id': new_waterpipeflowreading.id})
        else:
            readingperiodflowmeterline.write(
                {'waterpipeflowreading_id': new_waterpipeflowreading.id})
        return new_waterpipeflowreading.id
