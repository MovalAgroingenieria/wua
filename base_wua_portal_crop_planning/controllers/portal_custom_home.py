# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account
from odoo.exceptions import AccessError


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add enrolledsubparcels documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        enrolledsubparcels = request.env['wua.enrolledsubparcel']
        enrolledsubparcels_count = enrolledsubparcels.search_count(
            [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'enrolledsubparcels_count': enrolledsubparcels_count,
        })
        return response

    @http.route(['/my/enrolledsubparcels',
                 '/my/enrolledsubparcels/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_enrolledsubparcels(self, page=1, search=None,
                                     search_field=None,
                                     selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        enrolledsubparcels_model = request.env['wua.enrolledsubparcel']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'parcel_id': 'parcel_id.name',
                'subparcel_code': 'subparcel_code',
                'agriculturalseason_id': 'agriculturalseason_id.name',
                'subparceltype_id': 'subparceltype_id.name',
                'area_official': 'area_official',
                'cultivation_id': 'cultivation_id.name',
                'cultivationvariety_id': 'cultivationvariety_id.name',
                'irrigationsystem_id': 'irrigationsystem_id.name',
                'productionmethod_id': 'productionmethod_id.name',
                'profile': 'profile',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        enrolledsubparcels = enrolledsubparcels_model.search(domain)
        enrolledsubparcels_count = len(enrolledsubparcels)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/enrolledsubparcels",
            total=enrolledsubparcels_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_enrolledsubparcels = \
            enrolledsubparcels[offset:offset + items_per_page]
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        values.update({
            'enrolledsubparcels': paginated_enrolledsubparcels,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/enrolledsubparcels',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_crop_planning.portal_my_enrolledsubparcels",
            values)

    @http.route(['/my/cropplans', '/my/cropplans/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_cropplans(self, page=1, date_begin=None,
                            date_end=None, search=None,
                            search_field=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        cropplan_model = request.env['wua.cropplan']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            field_map = {
                'agriculturalseason_id': 'agriculturalseason_id.name',
                'request_date': 'request_date',
                'order_number': 'order_number',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        cropplan_count = cropplan_model.search_count(domain)
        pager = request.website.pager(
            url="/my/cropplans",
            total=cropplan_count,
            page=page,
            step=self._items_per_page
        )
        cropplans = \
            cropplan_model.search(
                domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'cropplans': cropplans,
            'partner': partner,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/cropplans',
            'cropplan_id_list': ','.join(map(str, cropplans.ids)),
        })
        return request.render(
            "base_wua_portal_crop_planning.portal_my_cropplans", values)

    @http.route(['/my/cropplans/<int:cropplan>'], type='http',
                auth="user", website=True)
    def cropplans_followup(self, cropplan=None, ids=None, **kw):
        cropplan = request.env['wua.cropplan'].browse([cropplan])
        try:
            cropplan.check_access_rights('read')
            cropplan.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        cropplan_sudo = cropplan.sudo()

        cropplan_id_list = [int(i) for i in ids.split(',')] if ids else []
        current_index = (
            cropplan_id_list.index(cropplan.id)
            if cropplan.id in cropplan_id_list else -1
        )
        prev_id = (
            cropplan_id_list[current_index - 1]
            if current_index > 0 else None
        )
        next_id = (
            cropplan_id_list[current_index + 1]
            if 0 <= current_index < len(cropplan_id_list) - 1 else None
        )
        return request.render("base_wua_portal_crop_planning.cropplans_followup", {
            'cropplan': cropplan_sudo,
            'partner': request.env.user.partner_id,
            'prev_cropplan_id': prev_id,
            'next_cropplan_id': next_id,
            'ids': ids,
            'cropplan_index': current_index + 1 if current_index >= 0 else 0,
            'cropplan_total': len(cropplan_id_list),
        })

    @http.route(['/my/enrolledsubparcels/<int:cropplan>/report'],
                type='http', auth="user", website=True)
    def enrolledsubparcels_followup_report(self, cropplan=None, **kw):
        """Generates the Partner report and serves it as a PDF"""
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        cropplan = request.env['wua.cropplan'].search([
            ('id', '=', cropplan),
            ('partner_id', '=', partner.id)
        ], limit=1)
        cropplan_model = request.env['wua.cropplan'].sudo()
        model_report = request.env['report'].sudo()
        cropplan = cropplan_model.search([('id', '=', cropplan.id)], limit=1)
        if not cropplan:
            return Response(
                "No cropplan found",
                status=404)
        report_ref = "base_wua_crop_planning.report_wua_cropplan"
        cropplan_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [cropplan.id], report_ref)

        response = request.make_response(
            cropplan_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_cropplan_report.pdf"')
            ]
        )
        return response