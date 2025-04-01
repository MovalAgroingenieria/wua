# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WizardImportRemotecontrolData(models.TransientModel):
    _inherit = 'wizard.import.remotecontrol.data'

    remotecontrol_type = fields.Selection(
        selection_add=[('icr', 'ICR Hidroweb')],
    )

    def import_reading_icr(self, json_data, date):
        reading_model = self.env['wua.reading'].with_context(
            icr_reading_date=date)
        readings = reading_model._get_readings_info_icr_from_json(
            json_data)
        readings = reading_model.refine_readings(readings)
        reading_model.save_readings(readings)
