# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add waterconnections documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        waterconnections = request.env['res.partner.waterconnection']
        waterconnection_count = waterconnections.search_count([
            ('partner_id', '=', partner.id),
        ])

        response.qcontext.update({
            'waterconnection_count': waterconnection_count,
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

        available_columns = [
            "water_connection",
            "description",
            "last_reading_time",
            "last_reading_value",
            "volume_real",
            "last_data_time",
            "last_total_volume",
            "last_waterflow",
            "last_valve_open",
            "last_valve_scheduled",
        ]

        values.update({
            'waterconnections': waterconnections,
            'partnerlinks': partnerlinks,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/waterconnections',
            'available_columns': available_columns,
        })
        return request.render(
            "base_wua_portal_infrastructure.portal_my_waterconnections",
            values)

    @http.route(['/my/waterconnections/<int:waterconnection>'],
                type='http', auth="user", website=True)
    def waterconnections_followup(self, waterconnection=None, **kw):
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

        return request.render(
            "base_wua_portal_infrastructure.waterconnections_followup", {
                'waterconnection': waterconnection_sudo,
                'partner':  request.env.user.partner_id,
                'gis_url': waterconnection.gis_viewer_link,
            })
