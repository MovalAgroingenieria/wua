# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add readings and presconsumptions documents to main account page"""
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

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
        response.qcontext.update({
            'readings_count': readings_count,
            'presconsumptions_count': presconsumptions_count,
        })
        return response

    @http.route(['/my/readings', '/my/readings/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_readings(self, page=1, search=None,
                           search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        waterconnection_partnerlink_model = \
            request.env['res.partner.waterconnection']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        waterconnections = \
            waterconnection_partnerlink_model.search(domain).mapped(
                'waterconnection_id')
        domain.append(('waterconnection_id', 'in', waterconnections.ids))
        readings_count = request.env['wua.reading'].search_count(domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/readings",
            total=readings_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        readings = request.env['wua.reading'].search(
            domain, limit=items_per_page, offset=offset)
        values.update({
            'readings': readings,
            'waterconnections': waterconnections,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/readings'
        })
        return request.render(
            "base_wua_portal_pressurized_irrigation.portal_my_readings",
            values)

    @http.route(['/my/presconsumptions',
                 '/my/presconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_presconsumptions(self, page=1, search=None,
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
                'watermeter': 'watermeter_id.name',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        waterconnections = \
            waterconnection_partnerlink_model.search(domain).mapped(
                'waterconnection_id')
        presconsumptions_domain = [
            ('waterconnection_id', 'in', waterconnections.ids)
        ]
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'reading_id': 'reading_id.name',
            }
            if search_field in field_map:
                presconsumptions_domain.append(
                    (field_map[search_field], 'ilike', search))

        presconsumptions_count = \
            request.env['wua.presconsumption'].search_count(
                presconsumptions_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/presconsumptions",
            total=presconsumptions_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        presconsumptions = request.env['wua.presconsumption'].search(
            presconsumptions_domain, limit=items_per_page, offset=offset)
        values.update({
            'presconsumptions': presconsumptions,
            'waterconnections': waterconnections,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/presconsumptions',
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation.portal_my_presconsumptions'
        return request.render(
            portal_view,
            values)
