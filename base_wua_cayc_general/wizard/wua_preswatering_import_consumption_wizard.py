# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import json
from odoo import models, fields, api, exceptions, _


class WuaPreswateringImportConsumptionWizard(models.TransientModel):
    _name = 'wua.preswatering.import.consumption.wizard'
    _description = 'Import SINEMA JSON from file'

    preswatering_id = fields.Many2one(
        string='Preswatering',
        comodel_name='wua.preswatering',
        required=True,
    )

    json_file = fields.Binary(
        string='JSON File (.json)',
        required=True,
    )

    json_filename = fields.Char(
        string='Filename',
    )

    @api.multi
    def action_import_consumptions(self):
        self.ensure_one()
        if not self.json_file:
            raise exceptions.UserError(_('You must upload a JSON file.'))
        try:
            content = base64.b64decode(self.json_file)
            raw_data = json.loads(content)
        except Exception as e:
            raise exceptions.UserError(_('Invalid JSON: %s') % str(e))
        data = {}
        for item in raw_data:
            try:
                name = item.get('variableName')
                value = float(item.get('value', 0))
                if value > 0 and name:
                    data[name] = value
            except Exception:
                continue
        if not data:
            raise exceptions.UserError(
                'No valid consumption data found in the file.')
        self.preswatering_id.with_context(
            overwrite_consumption_data=data,
        )._process_issued_nominal_flows(
            self.env['wua.presresconsumption'],
            self.preswatering_id,
        )
