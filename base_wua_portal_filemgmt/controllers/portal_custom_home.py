# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add files documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        files = request.env['res.file.partnerlink']
        files_count = files.search_count(
            [('partner_id', '=', partner.id)])
        registries = request.env['res.letter']
        domain = ['|',
                  ('recipient_partner_id', '=', partner.id),
                  ('sender_partner_id', '=', partner.id)]
        registries_count = registries.search_count(domain)
        response.qcontext.update({
            'files_count': files_count,
            'registries_count': registries_count,
        })
        return response

    @http.route(['/my/files', '/my/files/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_files(self, page=1, search=None,
                        search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        file_partnerlink_model = request.env['res.file.partnerlink']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'filename': 'file_id.name',
                'description': 'file_id.description',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        files_partnerlinks = file_partnerlink_model.search(domain)
        files = files_partnerlinks.mapped('file_id')
        files_count = len(files)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/files",
            total=files_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_files = files[offset:offset + items_per_page]
        values.update({
            'files': paginated_files,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/files',
        })
        return request.render(
            "base_wua_portal_filemgmt.portal_my_files",
            values)

    @http.route(['/my/registries', '/my/registries/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_registries(self, page=1, search=None,
                             search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        registry_model = request.env['res.letter']
        domain = ['|', ('recipient_partner_id', '=', partner.id),
                  ('sender_partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'registryname': 'name',
                'description': 'description',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        registries = registry_model.search(domain)
        registries_count = len(registries)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/registries",
            total=registries_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_registries = registries[offset:offset + items_per_page]
        values.update({
            'registries': paginated_registries.sudo(),
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/registries',
        })
        return request.render(
            "base_wua_portal_filemgmt.portal_my_registries",
            values)

    @http.route(['/my/files/<int:file_id>/report'],
                type='http', auth="user", website=True)
    def file_report(self, file_id=None, **kw):
        """Generates the File report and serves it as a PDF"""
        partner = request.env.user.partner_id
        partnerlink = request.env['res.file.partnerlink'].search([
            ('file_id', '=', file_id),
            ('partner_id', '=', partner.id)
        ], limit=1)
        file_record = partnerlink.file_id
        file_model = request.env['res.file'].sudo()
        model_report = request.env['report'].sudo()
        file_record = file_model.search([('id', '=', file_record.id)], limit=1)
        if not file_record:
            return Response(
                "No file found",
                status=404)

        category_report_map = {
            'resfilecategory_lease_file':
                'wua_crm_filemgmt.category_report_lease_document',
            'resfilecategory_trading_file':
                'wua_crm_filemgmt.category_report_trading_document',
            'resfilecategory_complaint_file':
                'wua_crm_filemgmt.category_report_complaint_document',
        }

        category_xml_id = request.env['ir.model.data'].sudo().search([
            ('model', '=', 'res.file.category'),
            ('res_id', '=', file_record.category_id.id),
        ], limit=1).name
        report = 'wua_crm_filemgmt.category_report_custom_document'
        report_ref = \
            category_report_map.get(category_xml_id, report)

        file_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [file_record.id], report_ref)

        response = request.make_response(
            file_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="file_report.pdf"')
            ]
        )
        return response

    @http.route(['/my/registries/<int:registry_id>/report'],
                type='http', auth="user", website=True)
    def registries_followup_report(self, registry_id=None, **kw):
        """Generates the Registry report and serves it as a PDF"""
        partner = request.env.user.partner_id
        registry = request.env['res.letter'].sudo().search([
            '|',
            ('recipient_partner_id', '=', partner.id),
            ('sender_partner_id', '=', partner.id),
            ('id', '=', registry_id)
        ], limit=1)
        if not registry:
            return Response(
                "No registry found",
                status=404)

        model_report = request.env['report'].sudo()
        report_ref = 'crm_lettermgmt.template_res_letter_report'
        registry_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [registry.id], report_ref)

        response = request.make_response(
            registry_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="registry_report.pdf"')
            ]
        )
        return response
