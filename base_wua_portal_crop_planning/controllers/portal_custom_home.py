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
        """ Add enrolledsubparcels documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

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
        enrolledsubparcels_model = request.env['wua.enrolledsubparcel']
        domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            field_map = {
                'parcel_id': 'parcel_id.name',
                'subparcel_code': 'subparcel_code',
                'cropplan_id': 'cropplan_id.name',
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
        values.update({
            'enrolledsubparcels': paginated_enrolledsubparcels,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/enrolledsubparcels',
        })
        return request.render(
            "base_wua_portal_crop_planning.portal_my_enrolledsubparcels",
            values)
