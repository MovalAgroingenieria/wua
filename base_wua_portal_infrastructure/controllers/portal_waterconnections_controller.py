# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add waterconnections documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        waterconnections = request.env['res.partner.waterconnection']
        waterconnection_count = waterconnections.search_count([
            ('partner_id', '=', partner.id),
        ])
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        response.qcontext.update({
            'waterconnection_count': waterconnection_count,
            'liquidation_on_portal': liquidation_on_portal,
        })
        return response

    @http.route(['/my/waterconnections',
                 '/my/waterconnections/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_waterconnections(
            self, page=1, search=None,
            search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        waterconnection_partnerlink_model = \
            request.env['res.partner.waterconnection']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            field_map = {
                'name': 'waterconnection_id.name',
                'description': 'waterconnection_id.description',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        waterconnection_count = \
            waterconnection_partnerlink_model.search_count(domain)
        pager = request.website.pager(
            url="/my/waterconnections",
            total=waterconnection_count,
            page=page,
            step=self._items_per_page,
        )
        partnerlinks = \
            waterconnection_partnerlink_model.search(
                domain, limit=self._items_per_page, offset=pager['offset'])
        waterconnections = \
            waterconnection_partnerlink_model.browse(
                partnerlinks.mapped('waterconnection_id').ids)
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        values.update({
            'waterconnections': waterconnections,
            'partnerlinks': partnerlinks,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/waterconnections',
            'waterconnection_id_list': ','.join(map(str, partnerlinks.ids)),
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_infrastructure.portal_my_waterconnections",
            values)

    @http.route(['/my/waterconnections/<int:waterconnection>'],
                type='http', auth="user", website=True)
    def waterconnections_followup(self, waterconnection=None, ids=None, **kw):
        partnerlink = \
            request.env['res.partner.waterconnection'].browse(
                [waterconnection])
        waterconnection = partnerlink.waterconnection_id
        try:
            waterconnection.check_access_rights('read')
            waterconnection.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        waterconnection_sudo = waterconnection.sudo()

        waterconnection_id_list = \
            [int(i) for i in ids.split(',')] if ids else []
        current_index = (
            waterconnection_id_list.index(partnerlink.id)
            if partnerlink.id in waterconnection_id_list else -1
        )
        prev_id = (
            waterconnection_id_list[current_index - 1]
            if current_index > 0 else None
        )
        next_id = (
            waterconnection_id_list[current_index + 1]
            if 0 <= current_index < len(waterconnection_id_list) - 1 else None
        )
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        return request.render(
            "base_wua_portal_infrastructure.waterconnections_followup", {
                'waterconnection': waterconnection_sudo,
                'partner':  partner,
                'gis_url': partner.gis_viewer_link,
                'prev_waterconnection_id': prev_id,
                'next_waterconnection_id': next_id,
                'ids': ids,
                'waterconnection_index':
                    current_index + 1 if current_index >= 0 else 0,
                'waterconnection_total': len(waterconnection_id_list),
                'liquidation_on_portal': liquidation_on_portal,
            })

    @http.route(['/my/waterconnections/<int:waterconnection>/report'],
                type='http', auth="user", website=True)
    def waterconnections_followup_report(self, waterconnection=None, **kw):
        """Generates the waterconnection report and serves it as a PDF"""
        user = request.env.user
        partnerlink = \
            request.env['res.partner.waterconnection'].search(
                [('waterconnection_id', '=', waterconnection)], limit=1)
        waterconnection = partnerlink.waterconnection_id
        try:
            waterconnection.check_access_rights('read')
            waterconnection.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        model_report = request.env['report'].sudo()
        if not waterconnection:
            return Response(
                "No waterconnection found",
                status=404)
        report_ref = \
            'base_wua_infrastructure.wua_waterconnection_technical_sheet_report_document'
        waterconnection_report = model_report.with_context(
            {'lang': user.partner_id.lang}).get_pdf(
                [waterconnection.id], report_ref)

        response = request.make_response(
            waterconnection_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_waterconnection_report.pdf"')
            ]
        )
        return response