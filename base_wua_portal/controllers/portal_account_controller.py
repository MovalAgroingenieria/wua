# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http, _
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account
from odoo.service import security


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        parcels = request.env['wua.parcel.partnerlink']
        parcel_count = parcels.search_count([('partner_id', '=', partner.id)])
        gis_viewer_link = partner.gis_viewer_link
        if gis_viewer_link and '&arg=' in gis_viewer_link:
            gis_viewer_link = gis_viewer_link.split('&arg=')[0]
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        response.qcontext.update({
            'parcel_count': parcel_count,
            'gis_viewer_link': gis_viewer_link,
            'liquidation_on_portal': liquidation_on_portal,
        })
        return response

    def _prepare_portal_layout_values(self):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
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
        partner = partner.parent_id or partner
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
