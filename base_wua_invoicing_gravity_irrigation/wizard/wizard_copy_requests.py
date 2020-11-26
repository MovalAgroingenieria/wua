# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WizardCopyRequests(models.TransientModel):
    _inherit = 'wizard.copy.requests'

    def do_copy(self, destination_wateringperiod_id, active_ids):
        source_wateringrequests = self.env['wua.wateringrequest'].browse(
            active_ids)
        for request in source_wateringrequests:
            if request.number_of_subparcels > 0:
                gravconsumption_ids = []
                for gravconsumption in request.gravconsumption_ids:
                    gravconsumption_vals = {
                        'subparcel_id': gravconsumption.subparcel_id.id,
                        'wateringperiod_id': destination_wateringperiod_id.id,
                        'watering_duration': gravconsumption.watering_duration,
                        }
                    gravconsumption_ids.append((0, 0, gravconsumption_vals))
                wateringrequest_vals = {
                    'wateringperiod_id': destination_wateringperiod_id.id,
                    'partner_id': request.partner_id.id,
                    'product_id': request.product_id.id,
                    'gravconsumption_ids': gravconsumption_ids,
                    }
            else:
                wateringrequest_vals = {
                    'wateringperiod_id': destination_wateringperiod_id.id,
                    'partner_id': request.partner_id.id,
                    'product_id': request.product_id.id,
                    }
            self.env['wua.wateringrequest'].create(wateringrequest_vals)
