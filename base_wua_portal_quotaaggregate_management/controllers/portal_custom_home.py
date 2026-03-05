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
        """ Add quotas and hydricmovements documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        quotaaggregates_count = \
            request.env['wua.quota.aggregatevalue'].search_count([
                ('partner_id', '=', partner.id),
            ])
        response.qcontext.update({
            'quotaaggregates_count': quotaaggregates_count,
        })
        return response

    @http.route(['/my/quotaaggregates', '/my/quotaaggregates/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_quotaaggregates(self, page=1, search=None,
                                  search_field=None, selected_columns=None,
                                  **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        quotaaggregates_model = \
            request.env['wua.quota.aggregatevalue']
        domain = [
            ('partner_id', '=', partner.id),
        ]
        if search and search_field:
            field_map = {
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        quotaaggregates = \
            quotaaggregates_model.search(domain)
        quotaaggregates_count = \
            request.env['wua.quota.aggregatevalue'].search_count(domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/quotaaggregates",
            total=quotaaggregates_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        quotaaggregates = request.env['wua.quota.aggregatevalue'].search(
            domain, limit=items_per_page, offset=offset)
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'quotaaggregates': quotaaggregates,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/quotaaggregates',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_quota_management.portal_my_quotaaggregates",
            values)
