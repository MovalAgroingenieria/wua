# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WizardRegularizeNegativeReading(models.TransientModel):
    _name = 'wizard.regularize.negative.reading'
    _description = 'Wizard to regularize negative readings'

    READING_TYPE = '03_real_partner'

    notes = fields.Html(
        string='Notes')

    @api.multi
    def action_regularize(self):
        self.ensure_one()
        reading_model = self.env['wua.reading']
        active_ids = self.env.context.get('active_ids', [])
        negative_readings = self.env['wua.negative.reading'].browse(
            active_ids)
        regularized = []
        errors = []
        for negative_reading in negative_readings:
            try:
                with self.env.cr.savepoint():
                    label = self._regularize_one(
                        negative_reading, reading_model)
                    regularized.append(label)
            except Exception as error:
                errors.append((negative_reading.display_name, str(error)))
        message = self._build_result_message(regularized, errors)
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Negative Reading Regularization Result'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': [
                {
                    'type': 'ir.actions.act_window_close',
                    'name': _('Close'),
                },
                {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'name': _('Refresh Page'),
                },
            ],
        }

    def _regularize_one(self, negative_reading, reading_model):
        watermeter = negative_reading.watermeter_id
        if not watermeter:
            raise exceptions.UserError(_(
                'The negative reading has no water meter.'))
        negative_time = negative_reading.reading_time
        negative_volume = negative_reading.volume
        previous_reading = reading_model.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '<', negative_time)],
            limit=1, order='reading_time desc')
        if not previous_reading:
            raise exceptions.UserError(_(
                'There is no previous reading for water meter "%s" before '
                '%s.') % (watermeter.display_name, negative_time))
        newer_reading = reading_model.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '>', negative_time)],
            limit=1, order='reading_time desc')
        if newer_reading:
            raise exceptions.UserError(_(
                'There are more recent readings for water meter "%s" (%s). '
                'It is not possible to regularize this negative reading.') % (
                    watermeter.display_name, newer_reading.reading_time))
        previous_volume = previous_reading.volume
        adjustement_volume = negative_volume - previous_volume
        if adjustement_volume >= 0:
            raise exceptions.UserError(_(
                'The regularization value for water meter "%s" is not a '
                'negative value (%.4f).') % (
                    watermeter.display_name, adjustement_volume))
        previous_time = fields.Datetime.from_string(
            previous_reading.reading_time)
        zero_reading_time = fields.Datetime.to_string(
            previous_time + datetime.timedelta(seconds=1))
        init_reading_time = fields.Datetime.to_string(
            previous_time + datetime.timedelta(seconds=2))
        zero_reading = reading_model.create({
            'watermeter_id': watermeter.id,
            'reading_time': zero_reading_time,
            'volume': previous_volume,
            'initialization_reading': False,
            'reading_type': self.READING_TYPE,
            'validated': False,
        })
        zero_reading.presconsumption_id.write({
            'adjustement_volume': adjustement_volume,
        })
        reading_model.create({
            'watermeter_id': watermeter.id,
            'reading_time': init_reading_time,
            'volume': negative_volume,
            'initialization_reading': True,
            'reading_type': self.READING_TYPE,
            'notes': self.notes,
            'validated': False,
        })
        return negative_reading.display_name

    def _build_result_message(self, regularized, errors):
        message_parts = []
        if regularized:
            regularized_list = ''.join([
                '<li style="color:green;font-weight:bold;">%s</li>' % name
                for name in regularized
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Negative readings successfully regularized'),
                    regularized_list))
        if errors:
            error_list = ''.join([
                '<li style="color:red;font-weight:bold;">%s: %s</li>' % (
                    name, msg)
                for name, msg in errors
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Negative readings with errors'), error_list))
        message = (
            '<div style="font-family:sans-serif">'
            '<p style="font-size:16px;margin-bottom:10px;">'
            '<b style="font-size:18px;color:#2c3e50;">%s</b>'
            '</p>%s</div>'
        ) % (
            _('Negative Reading Regularization Summary'),
            ''.join(message_parts),
        )
        return message
