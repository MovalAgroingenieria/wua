# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add parcels documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        parcels = request.env['wua.parcel.partnerlink']
        parcel_count = parcels.search_count([
            ('partner_id', '=', partner.id),
        ])
        gis_viewer_link = partner.gis_viewer_link
        if gis_viewer_link and '&arg=' in gis_viewer_link:
            gis_viewer_link = gis_viewer_link.split('&arg=')[0]
        response.qcontext.update({
            'parcel_count': parcel_count,
            'gis_viewer_link': gis_viewer_link,
        })
        return response

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }
        return values

    @http.route(['/my/parcels', '/my/parcels/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_parcels(self, page=1, date_begin=None,
                          date_end=None, search=None, search_field=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        parcel_partnerlink_model = request.env['wua.parcel.partnerlink']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            field_map = {
                'name': 'parcel_id.name',
                'extra_code': 'parcel_id.extra_code',
                'cadastral_reference': 'parcel_id.cadastral_reference',
                'concession': 'parcel_id.concession_ids.name',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        parcel_count = parcel_partnerlink_model.search_count(domain)
        pager = request.website.pager(
            url="/my/parcels",
            total=parcel_count,
            page=page,
            step=self._items_per_page
        )
        partnerlinks = \
            parcel_partnerlink_model.search(
                domain, limit=self._items_per_page, offset=pager['offset'])
        parcels = \
            parcel_partnerlink_model.browse(
                partnerlinks.mapped('parcel_id').ids)

        values.update({
            'parcels': parcels,
            'partnerlinks': partnerlinks,
            'partner': partner,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/parcels',
        })
        return request.render("base_wua_portal.portal_my_parcels", values)

    @http.route(['/my/parcels/<int:parcel>'],
                type='http', auth="user", website=True)
    def parcels_followup(self, parcel=None, **kw):
        partnerlink = request.env['wua.parcel.partnerlink'].browse([parcel])
        parcel = partnerlink.parcel_id
        try:
            parcel.check_access_rights('read')
            parcel.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        parcel_sudo = parcel.sudo()

        return request.render("base_wua_portal.parcels_followup", {
            'parcel': parcel_sudo,
            'partner': request.env.user.partner_id,
            'gis_url': parcel.gis_viewer_link,
        })

    @http.route('/my/report', type='http', auth="user", website=True)
    def portal_wua_partner_report(self, **kw):
        """Generates the Partner report and serves it as a PDF"""
        partner = request.env.user.partner_id
        partner_model = request.env['res.partner'].sudo()
        model_report = request.env['report'].sudo()
        partner = partner_model.search([('id', '=', partner.id)], limit=1)
        if not partner:
            return Response(
                "No partner found",
                status=404)
        report_ref = \
            'base_wua.wua_partner_report_document'
        partner_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [partner.id], report_ref)

        response = request.make_response(
            partner_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_partner_report.pdf"')
            ]
        )
        return response

    @http.route(['/my/parcels/<int:parcel>/report'],
                type='http', auth="user", website=True)
    def parcels_followup_report(self, parcel=None, **kw):
        """Generates the Partner report and serves it as a PDF"""
        partner = request.env.user.partner_id
        partnerlink = request.env['wua.parcel.partnerlink'].search([
            ('parcel_id', '=', parcel),
            ('partner_id', '=', partner.id)
        ], limit=1)
        parcel = partnerlink.parcel_id
        parcel_model = request.env['wua.parcel'].sudo()
        model_report = request.env['report'].sudo()
        parcel = parcel_model.search([('id', '=', parcel.id)], limit=1)
        if not parcel:
            return Response(
                "No parcel found",
                status=404)
        report_ref = \
            'base_wua.wua_parcel_report_document'
        parcel_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [parcel.id], report_ref)

        response = request.make_response(
            parcel_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_parcel_report.pdf"')
            ]
        )
        return response

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        response = \
            super(website_account, self).details(redirect=redirect, **post)
        partner = request.env.user.partner_id

        mandates = request.env['account.banking.mandate'].sudo().search([
            ('partner_id', '=', partner.id)
        ])

        if isinstance(response, dict):
            response.update({
                'mandates': mandates,
            })
        elif hasattr(response, 'qcontext'):
            response.qcontext.update({
                'mandates': mandates,
            })

        return response
