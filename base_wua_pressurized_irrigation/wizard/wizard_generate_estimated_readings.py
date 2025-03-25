# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, _
from odoo.exceptions import UserError


class WizardGenerateEstimatedReadings(models.TransientModel):
    _name = 'wizard.generate.estimated.readings'
    _description = 'Wizard to Generate Estimated Readings'

    date = fields.Datetime(
        string='Reading Date',
        required=True,
        default=fields.Datetime.now,
    )

    def action_generate_readings(self):
        active_ids = self.env.context.get('active_ids', [])
        waterconnections = self.env['wua.waterconnection'].browse(active_ids)
        for connection in waterconnections:
            last_reading = self.env['wua.reading'].search(
                [('waterconnection_id', '=', connection.id)],
                order='reading_time desc',
                limit=1,
            )
            last_value = last_reading.volume if last_reading else 0
            new_value = last_value + connection.estimated_monthly_consumption
            if connection.watermeter_id:
                reading_vals = {
                    'watermeter_id': connection.watermeter_id.id,
                    'reading_time': self.date,
                    'volume': new_value,
                    'reading_type': '01_estimated',
                    'validated': False,
                }
                if last_reading:
                    reading_vals['initialization_reading'] = False
                else:
                    reading_vals['initialization_reading'] = True
                self.env['wua.reading'].create(reading_vals)
            else:
                missing_watermeters = [
                    connection.display_name for connection
                    in waterconnections if not connection.watermeter_id]
                raise UserError(
                    _('The following Waterconnections need a Watermeter: %s')
                    % ', '.join(missing_watermeters))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Readings'),
            'res_model': 'wua.reading',
            'view_mode': 'tree,form',
            'domain': [('waterconnection_id', 'in', active_ids)],
        }
