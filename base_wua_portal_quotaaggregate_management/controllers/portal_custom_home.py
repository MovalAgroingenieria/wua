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
        quotaaggregates_count = \
            request.env['wua.quota.aggregatevalue'].search_count([
                ('partner_id', '=', partner.id)
            ])
        response.qcontext.update({
            'quotaaggregates_count': quotaaggregates_count,
        })
        return response

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
