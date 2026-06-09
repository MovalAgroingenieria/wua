# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add nrs documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        nrs = request.env['nrs.tracking']
        nrs_count = nrs.search_count(
            [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'nrs_count': nrs_count,
        })
        return response

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }
        return values

    @http.route(['/my/nrs', '/my/nrs/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_nrs(self, page=1, search=None,
                      search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        nrs_tracking_model = request.env['nrs.tracking']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'time': 'sms_time_data',
                'sender': 'sender',
                'invoice': 'invoice_id.name',
                'water_connection': 'waterconnection_id.name',
                'parcel': 'parcel_id.name',
                'subject': 'subject',
                'message': 'sms_message',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        has_waterconnection = \
            'waterconnection_id' in nrs_tracking_model._fields
        nrs = \
            nrs_tracking_model.search(domain, order='sms_time_data desc')
        nrs_count = len(nrs)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/nrs",
            total=nrs_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_nrs = nrs[offset:offset + items_per_page]
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        values.update({
            'nrs': paginated_nrs,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'has_waterconnection': has_waterconnection,
            'default_url': '/my/nrs',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_nrs.portal_my_nrs",
            values)
