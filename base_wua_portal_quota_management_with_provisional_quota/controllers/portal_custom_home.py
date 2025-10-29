# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    @http.route()
    def account(self, **kw):
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        waterconnection = request.env['res.partner.waterconnection']
        waterconnections = waterconnection.search(
            [('partner_id', '=', partner.id)]).mapped('waterconnection_id').ids
        current_controlperiod = request.env['wua.controlperiod'].search(
            [('state', '=', 'active')], limit=1)
        controlpresconsumptions_domain = [
            ('waterconnection_id', 'in', waterconnections)
        ]
        if current_controlperiod:
            controlpresconsumptions_domain.append(
                ('controlperiod_id', '=', current_controlperiod.id))
        cp_model = request.env['wua.controlpresconsumption']
        controlpresconsumptions_count = cp_model.search_count(
            controlpresconsumptions_domain)
        response.qcontext.update({
            'controlpresconsumptions_count': controlpresconsumptions_count,
        })
        return response