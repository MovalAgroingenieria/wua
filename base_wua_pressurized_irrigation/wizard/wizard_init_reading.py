# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, exceptions, _


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
    notes = fields.Html(
        string='Notes',
    )

    def _create_readings_in_model(self, model_name, vals):
        model = self.env[model_name]
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
