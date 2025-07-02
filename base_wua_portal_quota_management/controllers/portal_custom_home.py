# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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

        quota = request.env['wua.quota']
        quota_count = quota.search_count([
            ('partner_id', '=', partner.id),
            ('balance', '!=', 0)
        ])
        hydricmovement_count = request.env['wua.hydricmovement'].search_count([
            ('partner_id', '=', partner.id)
        ])
        quotaaggregates_count = \
            request.env['wua.quota.aggregatevalue'].search_count([
                ('partner_id', '=', partner.id)
            ])
        response.qcontext.update({
            'quota_count': quota_count,
            'hydricmovement_count': hydricmovement_count,
            'quotaaggregates_count': quotaaggregates_count,
        })
        return response

    @http.route(['/my/quotas', '/my/quotas/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_quotas(self, page=1, search=None,
                         search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        quota_model = \
            request.env['wua.quota']
        domain = [
            ('partner_id', '=', partner.id),
            '|',
            ('accumulated_input', '!=', 0),
            ('accumulated_consumption', '!=', 0),
        ]
        if search and search_field:
            field_map = {
                'period_initial_date': 'quotaperiod_id.initial_date',
                'period_end_date': 'quotaperiod_id.end_date',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        quotas = \
            quota_model.search(domain)
        quotas_count = request.env['wua.quota'].search_count(domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/quotas",
            total=quotas_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        quotas = request.env['wua.quota'].search(
            domain, limit=items_per_page, offset=offset)
        values.update({
            'quotas': quotas,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/quotas'
        })
        return request.render(
            "base_wua_portal_quota_management.portal_my_quotas",
            values)

    @http.route(['/my/quotaaggregates', '/my/quotaaggregates/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_quotaaggregates(self, page=1, search=None,
                                  search_field=None, selected_columns=None,
                                  **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        quotaaggregates_model = \
            request.env['wua.quota.aggregatevalue']
        domain = [
            ('partner_id', '=', partner.id)
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
        values.update({
            'quotaaggregates': quotaaggregates,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/quotaaggregates'
        })
        return request.render(
            "base_wua_portal_quota_management.portal_my_quotaaggregates",
            values)

    @http.route(['/my/hydricmovements',
                 '/my/hydricmovements/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_hydricmovements(self, page=1, search=None,
                                  search_field=None, selected_columns=None,
                                  **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        hydricmovement_model = \
            request.env['wua.hydricmovement']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            field_map = {
                'quota': 'quota_id.name',
                'watermeter': 'watermeter_id.name',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        hydricmovements = \
            hydricmovement_model.search(domain)
        hydricmovements_domain = [
        ]
        if search and search_field:
            field_map = {
                'quota': 'quota_id.name',
                'reading_id': 'reading_id.name',
                'event_time': 'event_time',
            }
            if search_field in field_map:
                hydricmovements_domain.append(
                    (field_map[search_field], 'ilike', search))

        hydricmovements_count = \
            request.env['wua.hydricmovement'].search_count(
                hydricmovements_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/hydricmovements",
            total=hydricmovements_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        hydricmovements = request.env['wua.hydricmovement'].search(
            hydricmovements_domain, limit=items_per_page, offset=offset)
        values.update({
            'hydricmovements': hydricmovements,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/hydricmovements',
        })
        portal_view = \
            'base_wua_portal_quota_management.portal_my_hydricmovements'
        return request.render(
            portal_view,
            values)
