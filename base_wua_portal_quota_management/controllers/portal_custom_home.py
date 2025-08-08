# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request, Response
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

        current_season = \
            request.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)

        domain = [
            ('partner_id', '=', partner.id),
            ('agriculturalseason_id', '=', current_season.id),
            ('quotaperiod_id.is_closed', '=', False),
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

        current_season = \
            request.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)
        hydricmovements_domain = [
            ('partner_id', '=', partner.id),
            ('agriculturalseason_id', '=', current_season.id),
            ('quotaperiod_id.is_closed', '=', False),
        ]
        if search and search_field:
            field_map = {
                'event_time': 'event_time',
                'water_type': 'superproduct_id.name',
                'description': 'description',
            }
            if search_field in field_map:
                hydricmovements_domain.append(
                    (field_map[search_field], 'ilike', search))

        hydricmovements = \
            hydricmovement_model.search(hydricmovements_domain)
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

    @http.route('/my/quotareport', type='http', auth="user", website=True)
    def portal_wua_partner_report(self, **kw):
        """Generates the Partner quotareport and serves it as a PDF"""
        partner = request.env.user.partner_id
        partner_model = request.env['res.partner'].sudo()
        model_report = request.env['report'].sudo()
        partner = partner_model.search([('id', '=', partner.id)], limit=1)
        if not partner:
            return Response(
                "No partner found",
                status=404)
        report_ref = \
            'base_wua_quota_management.wua_partner_quota_report_document'
        partner_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [partner.id], report_ref)

        response = request.make_response(
            partner_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_partner_quota_report.pdf"')
            ]
        )
        return response
