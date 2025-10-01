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
    notes = fields.Html(
        string='Notes',
    )

    def action_generate_init_readings(self):
        self.ensure_one()
        wc = self.waterconnection_id
        if not wc.watermeter_id:
            raise exceptions.UserError(
                _('This waterconnection has no watermeter assigned.')
            )
        reading = self.env['wua.reading']
        vals_final = {
            'watermeter_id': wc.watermeter_id.id,
            'waterconnection_id': wc.id,
            'reading_time': self.date_change,
            'volume': self.final_reading,
            'notes': self.notes,
            'initialization_reading': False,
        }
        reading.create(vals_final)
        vals_init = {
            'watermeter_id': wc.watermeter_id.id,
            'waterconnection_id': wc.id,
            'reading_time': fields.Datetime.to_string(
                fields.Datetime.from_string(self.date_change) +
                datetime.timedelta(seconds=1)
            ),
            'volume': self.initial_reading,
            'notes': self.notes,
            'initialization_reading': True,
        }
        reading.create(vals_init)
        return {'type': 'ir.actions.act_window_close'}
