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
        """ Add irrigationreports documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        irrigationreports = request.env['wua.irrigationreport']
        irrigationreports_count = irrigationreports.search_count(
            [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'irrigationreports_count': irrigationreports_count,
        })
        irrigationreport_requests = request.env['wua.reportrequest']
        irrigationreport_requests_count = \
            irrigationreport_requests.search_count(
                [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'irrigationreports_count': irrigationreports_count,
            'irrigationreport_requests_count': irrigationreport_requests_count,
        })
        return response

    @http.route(['/my/irrigationreports',
                 '/my/irrigationreports/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_irrigationreports(self, page=1, search=None,
                                    search_field=None,
                                    selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        irrigationreports_tracking_model = request.env['wua.irrigationreport']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'irrigationreport_number': 'name',
                'intake_id': 'intake_id.name',
                'watermeter_id': 'watermeter_id.name',
                'report_initial_time': 'report_initial_time',
                'report_end_time': 'report_end_time',
                'delivery_note': 'delivery_note',
                'volume': 'volume',
                'adjustement_volume': 'adjustement_volume',
                'volume_real': 'volume_real',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        irrigationreports = irrigationreports_tracking_model.search(domain)
        irrigationreports_count = len(irrigationreports)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/irrigationreports",
            total=irrigationreports_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_irrigationreports = \
            irrigationreports[offset:offset + items_per_page]
        values.update({
            'irrigationreports': paginated_irrigationreports,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/irrigationreports',
        })
        return request.render(
            "base_wua_portal_irrigation_report.portal_my_irrigationreports",
            values)

    @http.route(['/my/irrigationreports/<int:irrigationreport>/report'],
                type='http', auth="user", website=True)
    def irrigationreports_followup_report(self, irrigationreport=None, **kw):
        """Generates the irrigationreport report and serves it as a PDF"""
        partner = request.env.user.partner_id
        irrigationreport_model = request.env['wua.irrigationreport'].sudo()
        model_report = request.env['report'].sudo()
        irrigationreport = irrigationreport_model.search([
            ('id', '=', irrigationreport),
            ('partner_id', '=', partner.id)
        ], limit=1)
        if not irrigationreport:
            return Response(
                "No irrigationreport found",
                status=404)
        report_ref = \
            'base_wua_irrigation_report.report_wua_irrigationreport'
        irrigationreport_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [irrigationreport.id], report_ref)

        response = request.make_response(
            irrigationreport_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_irrigationreport_report.pdf"')
            ]
        )
        return response

    @http.route(['/my/irrigationreportrequests',
                 '/my/irrigationreportrequests/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_irrigationreportrequests(self, page=1, search=None,
                                           search_field=None,
                                           selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        irrigationreport_requests = request.env['wua.reportrequest']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'agriculturalseason_id': 'agriculturalseason_id.name',
                'request_date': 'request_date',
                'parcel_id': 'parcel_id.name',
                'product_id': 'product_id.name',
                'hours': 'hours',
                'volume': 'volume',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        irrigationreport_requests = irrigationreport_requests.search(domain)
        irrigationreport_requests_count = len(irrigationreport_requests)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/irrigationreportrequests",
            total=irrigationreport_requests_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_irrigationreport_requests = \
            irrigationreport_requests[offset:offset + items_per_page]
        values.update({
            'irrigationreportrequests': paginated_irrigationreport_requests,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/irrigationreportrequests',
        })
        return request.render(
            "base_wua_portal_irrigation_report" +
            ".portal_my_irrigationreportrequests",
            values)

    @http.route(['/my/irrigationreportrequests/<int:reportrequest>/report'],
                type='http', auth="user", website=True)
    def irrigationreport_request_followup_report(self,
                                                 reportrequest=None, **kw):
        """Generates the reportrequest report and serves it as a PDF"""
        partner = request.env.user.partner_id
        reportrequest_model = request.env['wua.reportrequest'].sudo()
        model_report = request.env['report'].sudo()
        reportrequest = reportrequest_model.search([
            ('id', '=', reportrequest),
            ('partner_id', '=', partner.id)
        ], limit=1)
        if not reportrequest:
            return Response(
                "No reportrequest found",
                status=404)
        report_ref = \
            'base_wua_irrigation_report_request' + \
            '.report_wua_irrigationreport_request'
        irrigationreport_report = model_report.with_context(
            {'lang': partner.lang}).get_pdf(
                [reportrequest.id], report_ref)

        response = request.make_response(
            irrigationreport_report,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename="wua_irrigationreport_report.pdf"')
            ]
        )
        return response