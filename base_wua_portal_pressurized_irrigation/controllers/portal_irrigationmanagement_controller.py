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
        waterconnection = request.env['res.partner.waterconnection']
        waterconnections = waterconnection.search(
            [('partner_id', '=', partner.id)]).mapped('waterconnection_id').ids
        readings_count = request.env['wua.reading'].search_count([
            ('waterconnection_id', 'in', waterconnections)
        ])
        presconsumptions_count = \
            request.env['wua.presconsumption'].search_count([
                ('waterconnection_id', 'in', waterconnections)
            ])
        values.update({
            'readings_count': readings_count,
            'presconsumptions_count': presconsumptions_count,
        })
        return values
