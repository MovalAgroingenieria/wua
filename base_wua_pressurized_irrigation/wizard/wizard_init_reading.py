# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WizardInitReading(models.TransientModel):
    _name = 'wizard.init.reading'
    _description = 'Wizard Initialize Water Meter Reading'

    waterconnection_id = fields.Many2one(
        comodel_name='wua.waterconnection',
        string='Water Connection',
        required=True,
        readonly=True,
    )
    date_change = fields.Datetime(
        string='Change Date',
        required=True,
        default=fields.Datetime.now,
    )
    final_reading = fields.Float(
        string='Final Reading',
        required=True,
        digits=(32, 4),
    )
    initial_reading = fields.Float(
        string='Initial Reading',
        required=True,
        digits=(32, 4),
    )
    regularization = fields.Boolean(
        string='Regularization',
        help='If checked, the final reading is registered like the negative '
             'reading transformation: a zero-consumption reading plus an '
             'adjustment, avoiding a negative consumption volume.',
    )
    last_reading_value = fields.Float(
        string='Last Reading Value',
        digits=(32, 4),
        readonly=True,
    )
    last_reading_time = fields.Datetime(
        string='Last Reading Time',
        readonly=True,
    )
    regularization_adjustment = fields.Float(
        string='Regularization Adjustment',
        digits=(32, 4),
        readonly=True,
        compute='_compute_regularization_adjustment',
        help='Difference (Reading to keep - Last Reading Value) applied as '
             'an adjustment on the zero-consumption reading.',
    )
    notes = fields.Html(
        string='Notes',
    )

    @api.depends('initial_reading', 'last_reading_value')
    def _compute_regularization_adjustment(self):
        for record in self:
            record.regularization_adjustment = (
                record.initial_reading - record.last_reading_value)

    @api.model
    def default_get(self, fields_list):
        res = super(WizardInitReading, self).default_get(fields_list)
        waterconnection_id = self.env.context.get(
            'default_waterconnection_id')
        if waterconnection_id:
            waterconnection = self.env['wua.waterconnection'].browse(
                waterconnection_id)
            res['last_reading_value'] = waterconnection.last_reading_value
            res['last_reading_time'] = waterconnection.last_reading_time
        return res

    def _get_previous_volume(self, model, watermeter_id, date):
        previous_reading = model.search(
            [('watermeter_id', '=', watermeter_id),
             ('reading_time', '<', date)],
            limit=1, order='reading_time desc')
        previous_volume = None
        if previous_reading:
            previous_volume = previous_reading.volume
        return previous_volume

    def _create_readings_in_model(self, model_name, vals):
        model = self.env[model_name]
        if self.regularization and 'presconsumption_id' in model._fields:
            previous_volume = self._get_previous_volume(
                model, vals['watermeter_id'], vals['date'])
            if previous_volume is None:
                raise exceptions.UserError(_(
                    'There is no previous reading to regularize for this '
                    'water meter.'))
            reg_reading = model.create({
                'watermeter_id': vals['watermeter_id'],
                'waterconnection_id': vals['waterconnection_id'],
                'reading_time': vals['date'],
                'volume': previous_volume,
                'notes': vals['notes'],
                'initialization_reading': False,
                'reading_type': '02_real_worker',
            })
            if reg_reading.presconsumption_id:
                reg_reading.presconsumption_id.write({
                    'adjustement_volume':
                        vals['init_value'] - previous_volume,
                })
        else:
            model.create({
                'watermeter_id': vals['watermeter_id'],
                'waterconnection_id': vals['waterconnection_id'],
                'reading_time': vals['date'],
                'volume': vals['final_value'],
                'notes': vals['notes'],
                'initialization_reading': False,
                'reading_type': '02_real_worker',
            })
        model.create({
            'watermeter_id': vals['watermeter_id'],
            'waterconnection_id': vals['waterconnection_id'],
            'reading_time': fields.Datetime.to_string(
                fields.Datetime.from_string(vals['date']) +
                datetime.timedelta(seconds=1),
            ),
            'volume': vals['init_value'],
            'notes': vals['notes'],
            'initialization_reading': True,
            'reading_type': '02_real_worker',
        })

    def action_generate_init_readings(self):
        self.ensure_one()
        wc = self.waterconnection_id
        if not wc.watermeter_id:
            raise exceptions.UserError(
                _('This waterconnection has no watermeter assigned.'),
            )
        vals = {
            'watermeter_id': wc.watermeter_id.id,
            'waterconnection_id': wc.id,
            'date': self.date_change,
            'final_value': self.final_reading,
            'init_value': self.initial_reading,
            'notes': self.notes,
        }
        self._create_readings_in_model('wua.reading', vals)
        return {'type': 'ir.actions.act_window_close'}
