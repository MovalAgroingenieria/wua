# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class PortalIrrigationManagement(http.Controller):

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        values = \
            super(
                PortalIrrigationManagement, self
            )._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        tankconsumptions_count = \
            request.env['wua.tankconsumption'].search_count([
                ('partner_id', '=', partner.id)
            ])
        values.update({
            'tankconsumptions_count': tankconsumptions_count,
        })
        return values
