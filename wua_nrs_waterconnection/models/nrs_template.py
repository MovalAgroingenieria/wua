# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
import random
from odoo import models, fields, exceptions, _


class NRSTemplate(models.Model):
    _inherit = 'nrs.template'

    type = fields.Selection(
        selection_add=[('waterconnection', 'Waterconnection')])

    def _get_random_waterconnection(self):
        waterconnection = ""
        waterconnection_ids = \
            self.env['wua.waterconnection'].search([], limit=1000).ids
        if len(waterconnection_ids) > 0:
            random_waterconnection_id = random.choice(waterconnection_ids)
            waterconnection = self.env['wua.waterconnection'].browse(
                random_waterconnection_id)
        else:
            raise exceptions.ValidationError(_("No waterconnection found"))
        return waterconnection

    def _get_template_render_context_waterconnection(self):
        waterconnection = self._get_random_waterconnection()
        if waterconnection.irrigationpoint_ids:
            partner = waterconnection.irrigationpoint_ids[0].partner_id
        else:
            partner = self._get_random_partner()
        render_context = {
            "partner": partner, "waterconnection": waterconnection,
            "datetime": datetime}
        return render_context
