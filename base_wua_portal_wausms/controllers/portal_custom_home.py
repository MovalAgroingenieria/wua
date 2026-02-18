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
        """ Add wausms documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        wausms = request.env['wausms.tracking']
        wausms_count = wausms.search_count(
            [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'wausms_count': wausms_count,
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

    @http.route(['/my/wausms', '/my/wausms/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_wausms(self, page=1, search=None,
                         search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        wausms_tracking_model = request.env['wausms.tracking']
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
            'waterconnection_id' in wausms_tracking_model._fields
        wausms = \
            wausms_tracking_model.search(domain, order='sms_time_data desc')
        wausms_count = len(wausms)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/wausms",
            total=wausms_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_wausms = wausms[offset:offset + items_per_page]
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        values.update({
            'wausms': paginated_wausms,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'has_waterconnection': has_waterconnection,
            'default_url': '/my/wausms',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_wausms.portal_my_wausms",
            values)
