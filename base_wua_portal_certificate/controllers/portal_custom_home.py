# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account
from werkzeug.utils import redirect


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add certificates documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        certificates_count = request.env['wua.certificate'].search_count([
            ('partner_id', '=', partner.id)
        ])
        response.qcontext.update({
            'certificates_count': certificates_count,
        })
        return response

    @http.route(['/my/certificates', '/my/certificates/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_certificates(self, page=1, search=None,
                               search_field=None,
                               selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'name': 'name',
                'certificatetype': 'certificatetype_id.name',
                'date_of_issue': 'date_of_issue',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        certificates_count = \
            request.env['wua.certificate'].search_count(domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/certificates",
            total=certificates_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        certificates = request.env['wua.certificate'].search(
            domain, limit=items_per_page, offset=offset)
        max_pending_certificates = request.env['ir.values'].get_default(
            'wua.configuration', 'max_pending_certificates')
        pending_certificates = request.env['wua.certificate'].search(
            [('partner_id', '=', partner.id), ('state', '=', '01_draft')])
        can_request_certificate = True
        if pending_certificates:
            num_pending_certificates = len(pending_certificates)
            if num_pending_certificates >= max_pending_certificates:
                can_request_certificate = False
        certificatetype_model = request.env['wua.certificate.type']
        values.update({
            'certificates': certificates,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/certificates',
            'can_request_certificate': can_request_certificate,
            'certificate_types': certificatetype_model.sudo().search([]),
        })
        return request.render(
            "base_wua_portal_certificate.portal_my_certificates",
            values)

    @http.route('/my/certificate/<int:certificate_id>/report',
                type='http', auth="user", website=True)
    def portal_wua_certificate_report(self, certificate_id, **kw):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        certificate = request.env['wua.certificate'].sudo().search([
            ('id', '=', certificate_id),
            ('partner_id', '=', partner.id)
        ], limit=1)
        if not certificate or not certificate.document:
            return request.not_found()

        pdf_data = base64.b64decode(certificate.document)

        return request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="{}_report.pdf"'.format(
                     certificate.name)),
            ]
        )

    @http.route('/my/certificate/request', type='http', auth='user',
                methods=['POST'], csrf=False, website=True)
    def portal_create_certificate(self, **post):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        certificatetype_id = \
            request.env['wua.certificate.type'].sudo().search([
                ('id', '=', int(post.get('certificatetype_id')))
                ], limit=1)
        notes = post.get('notes', '')
        main_page = certificatetype_id.main_page
        final_paragraph = certificatetype_id.final_paragraph
        requested_from_portal = True,
        user_who_signs_id = \
            request.env.user.company_id.employee_as_secretary_id.id
        if partner.lang:
            main_page = certificatetype_id.with_context(
                {'lang': partner.lang}).main_page
            final_paragraph = certificatetype_id.with_context(
                {'lang': partner.lang}).final_paragraph
        fields_of_new_certificate = {
            'partner_id': partner.id,
            'certificatetype_id': certificatetype_id.id,
            'requested_from_portal': True,
            'user_who_signs_id': user_who_signs_id,
            'main_page': main_page,
            'final_paragraph': final_paragraph,
            }
        if notes:
            notes = '<p>' + notes + '<br></p>'
            if requested_from_portal:
                fields_of_new_certificate['notes_user'] = notes
            else:
                fields_of_new_certificate['notes_wua'] = notes
        new_certificate = request.env['wua.certificate'].sudo().create(
            fields_of_new_certificate)
        only_parcels_as_main = request.env['ir.values'].get_default(
            'wua.configuration', 'only_parcels_as_main')
        model_partnerlinks = request.env['wua.parcel.partnerlink'].sudo()
        conditions = [('partner_id', '=', partner.id)]
        if only_parcels_as_main:
            conditions.append(
                ('parcel_id.partner_id', '=', partner.id))
        partnerlinks = model_partnerlinks.search(conditions)
        for partnerlink in (partnerlinks or []):
            add_parcel = \
                ((certificatetype_id.include_parcel_if_owner and
                 partnerlink.profile == 'O') or
                 (certificatetype_id.include_parcel_if_lessee and
                 partnerlink.profile == 'L') or
                 (certificatetype_id.include_parcel_if_payer and
                 partnerlink.profile == 'P'))
            create_certificate = \
                request.env['wizard.create.certificate'].sudo()
            if add_parcel:
                fields_of_new_certificateparcel = \
                    create_certificate._get_fields_of_new_certificate(
                        new_certificate, partnerlink)
                request.env['wua.certificate.parcel'].sudo().create(
                    fields_of_new_certificateparcel)
        return redirect('/my/certificates')
