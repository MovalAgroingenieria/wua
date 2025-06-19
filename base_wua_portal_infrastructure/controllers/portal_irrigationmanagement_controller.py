# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class PortalIrrigationManagement(http.Controller):

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        waterconnections = request.env['res.partner.waterconnection']
        waterconnection_count = waterconnections.search_count([
            ('partner_id', '=', partner.id),
        ])
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner,
            'waterconnection_count': waterconnection_count,
        }
        return values

    @http.route(['/my/irrigationmanagement'],
                type='http', auth="user", website=True)
    def portal_my_irrigationmanagement(self):
        """ Redirects to the irrigation management portal page """
        values = self._prepare_portal_layout_values()
        return request.render(
            "base_wua_portal_infrastructure.portal_my_irrigationmanagement",
            values)
