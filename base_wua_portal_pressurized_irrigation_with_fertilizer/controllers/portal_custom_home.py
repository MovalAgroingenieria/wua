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
        """ Add readings and fertconsumptions documents to main account page"""
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        waterconnection = request.env['res.partner.waterconnection']
        waterconnections = waterconnection.search(
            [('partner_id', '=', partner.id)]).mapped('waterconnection_id').ids
        fertconsumptions_count = \
            request.env['wua.fertconsumption'].search_count([
                ('waterconnection_id', 'in', waterconnections)
            ])
        response.qcontext.update({
            'fertconsumptions_count': fertconsumptions_count,
        })
        return response

    @http.route(['/my/fertconsumptions',
                 '/my/fertconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_fertconsumptions(self, page=1, search=None,
                                   search_field=None, selected_columns=None,
                                   **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        waterconnection_partnerlink_model = \
            request.env['res.partner.waterconnection']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        waterconnections = \
            waterconnection_partnerlink_model.search(domain).mapped(
                'waterconnection_id')
        fertconsumptions_domain = [
            ('waterconnection_id', 'in', waterconnections.ids),
            ('validated', '=', True)
        ]
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'product': 'product_id.name',
                'date': 'date',
            }
            if search_field in field_map:
                if search_field == 'date':
                    search_date = search.strip()
                    fertconsumptions_domain.append(
                        ('reading_initial_time',
                         'ilike', search_date))
                    fertconsumptions_domain.append(
                        ('reading_end_time',
                         'ilike', search_date))
                else:
                    fertconsumptions_domain.append(
                        (field_map[search_field], 'ilike', search))

        fertconsumptions_count = \
            request.env['wua.fertconsumption'].search_count(
                fertconsumptions_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/fertconsumptions",
            total=fertconsumptions_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        fertconsumptions = request.env['wua.fertconsumption'].search(
            fertconsumptions_domain, limit=items_per_page, offset=offset,
            order="reading_initial_time desc")
        values.update({
            'fertconsumptions': fertconsumptions,
            'waterconnections': waterconnections,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/fertconsumptions',
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation_with_fertilizer' + \
            '.portal_my_fertconsumptions'
        return request.render(
            portal_view,
            values)
