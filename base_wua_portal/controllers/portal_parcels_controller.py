# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request, Response


class PortalParcels(http.Controller):

    _items_per_page = 10

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
        has_extra_code = '' in parcel_partnerlink_model._fields
        values.update({
            'parcels': parcels,
            'partnerlinks': partnerlinks,
            'partner': partner,
            'pager': pager,
            'search_query': search,
            'has_extra_code': has_extra_code,
            'search_field': search_field,
            'default_url': '/my/parcels',
            'parcel_id_list': ','.join(map(str, partnerlinks.ids)),
        })
        return request.render("base_wua_portal.portal_my_parcels", values)

    @http.route(['/my/parcels/<int:parcel>'], type='http',
                auth="user", website=True)
    def parcels_followup(self, parcel=None, ids=None, **kw):
        partnerlink = request.env['wua.parcel.partnerlink'].browse([parcel])
        parcel = partnerlink.parcel_id
        try:
            parcel.check_access_rights('read')
            parcel.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        parcel_sudo = parcel.sudo()

        parcel_id_list = [int(i) for i in ids.split(',')] if ids else []
        current_index = (
            parcel_id_list.index(partnerlink.id)
            if partnerlink.id in parcel_id_list else -1
        )
        prev_id = (
            parcel_id_list[current_index - 1]
            if current_index > 0 else None
        )
        next_id = (
            parcel_id_list[current_index + 1]
            if 0 <= current_index < len(parcel_id_list) - 1 else None
        )
        url = request.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        parcel_param = request.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        if (url and parcel_param):
            gis_viewer_link = url + '?' + parcel_param + '=' + parcel.name
        return request.render("base_wua_portal.parcels_followup", {
            'parcel': parcel_sudo,
            'partner': request.env.user.partner_id,
            'gis_url': gis_viewer_link,
            'prev_parcel_id': prev_id,
            'next_parcel_id': next_id,
            'ids': ids,
            'parcel_index': current_index + 1 if current_index >= 0 else 0,
            'parcel_total': len(parcel_id_list),
        })

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
