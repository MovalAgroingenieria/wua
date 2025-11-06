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
        """ Add readings and presconsumptions documents to main account page"""
        response = super(website_account, self).account(**kw)
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
        partner = partner.parent_id or partner
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
        domain.append(('validated', '=', True))
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
                'reading_time': 'reading_time',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
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
        partner = partner.parent_id or partner
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
            ('waterconnection_id', 'in', waterconnections.ids),
            ('reading_id.validated', '=', True)
        ]
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'reading_id': 'reading_id.name',
                'date': 'date',
            }
            if search_field in field_map:
                if search_field == 'date':
                    search_date = search.strip()
                    presconsumptions_domain.append(
                        ('reading_initial_time',
                         'ilike', search_date))
                    presconsumptions_domain.append(
                        ('reading_end_time',
                         'ilike', search_date))
            else:
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

    @http.route(['/my/irrigationevents',
                 '/my/irrigationevents/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_irrigationevents(self, page=1, search=None,
                                   search_field=None, selected_columns=None,
                                   **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
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
        irrigationevents_domain = [
            ('waterconnection_id', 'in', waterconnections.ids)
        ]
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'date': 'date',
            }
            if search_field in field_map:
                if search_field == 'date':
                    search_date = search.strip()
                    irrigationevents_domain.append(
                        ('irrigation_start_date', 'ilike', search_date))
                    irrigationevents_domain.append(
                        ('irrigation_end_date', 'ilike', search_date))
            else:
                irrigationevents_domain.append(
                    (field_map[search_field], 'ilike', search))
        irrigationevent_count = \
            request.env['wua.waterconnection.irrigation.event'].search_count(
                irrigationevents_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/irrigationevents",
            total=irrigationevent_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        irrigationevents = \
            request.env['wua.waterconnection.irrigation.event'].search(
                irrigationevents_domain, limit=items_per_page, offset=offset)
        values.update({
            'irrigationevents': irrigationevents,
            'waterconnections': waterconnections,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/irrigationevents',
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation.portal_my_irrigationevents'
        return request.render(
            portal_view,
            values)
