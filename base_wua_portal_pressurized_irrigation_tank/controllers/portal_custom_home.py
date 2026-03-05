# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add readings and tankconsumptions documents to main account page"""
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        tankconsumptions_count = \
            request.env['wua.tankconsumption'].search_count([
                ('partner_id', '=', partner.id),
            ])
        response.qcontext.update({
            'tankconsumptions_count': tankconsumptions_count,
        })
        return response

    @http.route(['/my/tankconsumptions',
                 '/my/tankconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_tankconsumptions(self, page=1, search=None,
                                   search_field=None, selected_columns=None,
                                   **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        tankconsumptions_domain = [
            ('partner_id', '=', partner.id),
        ]
        if search and search_field:
            field_map = {
                'initial_time': 'initial_time',
                'end_time': 'end_time',
                'tank': 'tank_id.name',
            }
            if search_field in field_map:
                tankconsumptions_domain.append(
                    (field_map[search_field], 'ilike', search))

        tankconsumptions_count = \
            request.env['wua.tankconsumption'].search_count(
                tankconsumptions_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/tankconsumptions",
            total=tankconsumptions_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        tankconsumptions = request.env['wua.tankconsumption'].search(
            tankconsumptions_domain, limit=items_per_page, offset=offset,
            order="initial_time desc")
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'tankconsumptions': tankconsumptions,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/tankconsumptions',
            'liquidation_on_portal': liquidation_on_portal,
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation_tank' + \
            '.portal_my_tankconsumptions'
        return request.render(
            portal_view,
            values)
