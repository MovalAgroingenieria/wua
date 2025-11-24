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
        """Add pressurized irrigation requests and consumptions to main
        account page
        """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        current_season = \
            request.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)

        preswateringrequest_domain = [
            ('partner_id', '=', partner.id),
        ]
        if current_season:
            preswateringrequest_domain.append(
                ('agriculturalseason_id', '=', current_season.id))

        preswateringrequest_count = \
            request.env['wua.preswateringrequest'].search_count(
                preswateringrequest_domain)

        presresconsumption_domain = [
            ('partner_id', '=', partner.id),
        ]
        if current_season:
            presresconsumption_domain.append(
                ('agriculturalseason_id', '=', current_season.id))

        presresconsumption_count = \
            request.env['wua.presresconsumption'].search_count(
                presresconsumption_domain)

        response.qcontext.update({
            'preswateringrequest_count': preswateringrequest_count,
            'presresconsumption_count': presresconsumption_count,
        })
        return response

    @http.route(['/my/preswateringrequests',
                 '/my/preswateringrequests/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_preswateringrequests(self, page=1, search=None,
                                       search_field=None,
                                       preswateringperiod_id=None,
                                       filter_is_open=None, **kw):
        """Portal view for pressurized irrigation requests"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        current_season = \
            request.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)

        domain = [
            ('partner_id', '=', partner.id),
        ]
        if current_season:
            domain.append(('agriculturalseason_id', '=', current_season.id))

        if preswateringperiod_id:
            domain.append(
                ('preswateringperiod_id', '=', int(preswateringperiod_id)),
                )

        if filter_is_open:
            if filter_is_open == 'open':
                domain.append(('is_open', '=', True))
            elif filter_is_open == 'closed':
                domain.append(('is_open', '=', False))

        if search and search_field:
            field_map = {
                'initial_date': 'initial_date',
                'period': 'preswateringperiod_id.name',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        preswateringrequests = \
            request.env['wua.preswateringrequest'].search(
                domain, order='initial_date desc')
        preswateringrequests_count = \
            request.env['wua.preswateringrequest'].search_count(domain)

        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/preswateringrequests",
            total=preswateringrequests_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'preswateringperiod_id': preswateringperiod_id,
                'filter_is_open': filter_is_open,
            },
        )

        offset = (page - 1) * items_per_page
        preswateringrequests = request.env['wua.preswateringrequest'].search(
            domain, limit=items_per_page, offset=offset,
            order='preswateringperiod_id, is_open desc, initial_date desc')

        # Group by period and is_open for visual grouping
        grouped_requests = {}
        for req in preswateringrequests:
            period_name = (
                req.preswateringperiod_id.display_name
                if req.preswateringperiod_id else 'No Period'
            )
            is_open_label = 'Open' if req.is_open else 'Closed'

            if period_name not in grouped_requests:
                grouped_requests[period_name] = {'Open': [], 'Closed': []}

            grouped_requests[period_name][is_open_label].append(req)

        preswateringperiods = request.env['wua.preswateringperiod'].search([
            ('agriculturalseason_id', '=', current_season.id),
        ], order='initial_date desc')

        values.update({
            'preswateringrequests': preswateringrequests,
            'grouped_requests': grouped_requests,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/preswateringrequests',
            'preswateringperiods': preswateringperiods,
            'selected_preswateringperiod_id': (
                int(preswateringperiod_id) if preswateringperiod_id else None
            ),
            'filter_is_open': filter_is_open,
            'partner': partner,
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation_request.' \
            'portal_my_preswateringrequests'
        return request.render(portal_view, values)

    @http.route(['/my/preswateringrequest/<int:request_id>'],
                type='http', auth="user", website=True)
    def portal_my_preswateringrequest_detail(self, request_id, **kw):
        """Portal view for a single pressurized irrigation request with its
        consumptions
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        # Get the irrigation request
        preswateringrequest = request.env['wua.preswateringrequest'].search([
            ('id', '=', request_id),
            ('partner_id', '=', partner.id),
        ], limit=1)

        if not preswateringrequest:
            return request.redirect('/my/preswateringrequests')

        # Get associated consumptions
        presresconsumptions = request.env['wua.presresconsumption'].search([
            ('preswateringrequest_id', '=', preswateringrequest.id),
        ], order='request_date desc, initial_hour asc')

        values.update({
            'preswateringrequest': preswateringrequest,
            'presresconsumptions': presresconsumptions,
            'partner': partner,
            'page_name': 'preswateringrequest_detail',
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation_request.' \
            'portal_my_preswateringrequest_detail'
        return request.render(portal_view, values)

    @http.route(['/my/presresconsumptions',
                 '/my/presresconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_presresconsumptions(self, page=1, search=None,
                                      search_field=None,
                                      preswateringperiod_id=None, **kw):
        """Portal view for pressurized irrigation request consumptions"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        current_season = \
            request.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)

        domain = [
            ('partner_id', '=', partner.id),
        ]
        if current_season:
            domain.append(('agriculturalseason_id', '=', current_season.id))

        if preswateringperiod_id:
            domain.append(
                ('preswateringperiod_id', '=', int(preswateringperiod_id)),
                )

        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'request_date': 'request_date',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        presresconsumptions = \
            request.env['wua.presresconsumption'].search(
                domain, order='request_date desc')
        presresconsumptions_count = \
            request.env['wua.presresconsumption'].search_count(domain)

        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/presresconsumptions",
            total=presresconsumptions_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'preswateringperiod_id': preswateringperiod_id,
            },
        )

        offset = (page - 1) * items_per_page
        presresconsumptions = request.env['wua.presresconsumption'].search(
            domain, limit=items_per_page, offset=offset,
            order='request_date desc')

        preswateringperiods = request.env['wua.preswateringperiod'].search([
            ('agriculturalseason_id', '=', current_season.id),
        ], order='initial_date desc')

        values.update({
            'presresconsumptions': presresconsumptions,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/presresconsumptions',
            'preswateringperiods': preswateringperiods,
            'selected_preswateringperiod_id': (
                int(preswateringperiod_id) if preswateringperiod_id else None
            ),
            'partner': partner,
        })
        portal_view = \
            'base_wua_portal_pressurized_irrigation_request.' \
            'portal_my_presresconsumptions'
        return request.render(portal_view, values)
