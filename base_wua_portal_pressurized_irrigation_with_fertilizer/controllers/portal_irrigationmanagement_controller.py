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
        waterconnection = request.env['res.partner.waterconnection']
        waterconnections = waterconnection.search(
            [('partner_id', '=', partner.id)]).mapped('waterconnection_id').ids
        fertconsumptions_count = \
            request.env['wua.fertconsumption'].search_count([
                ('waterconnection_id', 'in', waterconnections)
            ])
        values.update({
            'fertconsumptions_count': fertconsumptions_count,
        })
        return values
