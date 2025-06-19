# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.exceptions import AccessDenied
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account
from odoo.service import security


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        parcels = request.env['wua.parcel.partnerlink']
        parcel_count = parcels.search_count([('partner_id', '=', partner.id)])
        gis_viewer_link = partner.gis_viewer_link
        if gis_viewer_link and '&arg=' in gis_viewer_link:
            gis_viewer_link = gis_viewer_link.split('&arg=')[0]
        response.qcontext.update({
            'parcel_count': parcel_count,
            'gis_viewer_link': gis_viewer_link,
        })
        return response

    def _prepare_portal_layout_values(self):
        partner = request.env.user.partner_id
        return {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        response = \
            super(website_account, self).details(redirect=redirect, **post)
        partner = request.env.user.partner_id
        mandates = request.env['account.banking.mandate'].sudo().search([
            ('partner_id', '=', partner.id)
        ])
        company = request.website.company_id
        response.qcontext.update({
            'company_email': company.email,
        })
        if isinstance(response, dict):
            response.update({
                'mandates': mandates,
            })
        elif hasattr(response, 'qcontext'):
            response.qcontext.update({
                'mandates': mandates,
            })

        return response

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

    @http.route(['/my/change_password'], type='http',
                auth='user', website=True)
    def change_password_form(self, **kwargs):
        return request.render('base_wua_portal.change_password_template', {})

    @http.route(['/my/change_password/submit'], type='http', auth='user',
                methods=['POST'], website=True, csrf=True)
    def change_password_submit(self, old_password, new_password,
                               confirm_password, **kwargs):
        user = request.env.user

        if new_password == old_password:
            return request.render('base_wua_portal.change_password_template', {
                'error': _('Old and new passwords cannot be the same.'),
            })

        if new_password != confirm_password:
            return request.render('base_wua_portal.change_password_template', {
                'error': _('New passwords do not match.'),
            })

        try:
            security.check(request.db, user.id, old_password)

            user.sudo().write({'password': new_password})
            return request.render('base_wua_portal.change_password_template', {
                'success': _('Password updated successfully.'),
            })

        except AccessDenied:
            return request.render('base_wua_portal.change_password_template', {
                'error': _('Old password is incorrect.'),
            })
