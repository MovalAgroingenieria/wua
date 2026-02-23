# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 20

    @http.route()
    def account(self, **kw):
        """Add gravity irrigation consumptions count to main account page"""
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        gravconsumption_count = request.env[
            'wua.gravconsumption'].sudo().search_count(
            [('partner_id', '=', partner.id)])

        response.qcontext.update({
            'gravconsumption_count': gravconsumption_count,
        })
        return response

    @http.route(['/my/gravconsumptions',
                 '/my/gravconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_gravconsumptions(self, page=1, search=None,
                                   search_field=None,
                                   wateringperiod_id=None,
                                   filter_state=None, **kw):
        """Portal view for gravity irrigation consumptions"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        domain = [('partner_id', '=', partner.id)]

        if wateringperiod_id:
            try:
                domain.append(
                    ('wateringperiod_id', '=', int(wateringperiod_id)))
            except (ValueError, TypeError):
                pass

        if filter_state in ('proposed', 'planned', 'executed'):
            domain.append(('state', '=', filter_state))

        if search and search_field:
            field_map = {
                'watering': 'watering_id.name',
                'parcel': 'parcel_id.name',
                'irrigationditch': 'irrigationditch_id.name',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        gravconsumptions_count = request.env[
            'wua.gravconsumption'].sudo().search_count(domain)

        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/gravconsumptions",
            total=gravconsumptions_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'wateringperiod_id': wateringperiod_id,
                'filter_state': filter_state,
            },
        )

        offset = (page - 1) * items_per_page
        gravconsumptions = request.env['wua.gravconsumption'].sudo().search(
            domain,
            limit=items_per_page,
            offset=offset,
            order='wateringperiod_id desc, state, name')

        # Group by period name and state for visual display
        grouped_consumptions = {}
        for cons in gravconsumptions:
            period_name = (
                cons.wateringperiod_id.display_name
                if cons.wateringperiod_id else 'No Period'
            )
            state_label = {
                'proposed': 'Proposed',
                'planned': 'Planned',
                'executed': 'Executed',
            }.get(cons.state, cons.state)

            if period_name not in grouped_consumptions:
                grouped_consumptions[period_name] = {
                    'Proposed': [], 'Planned': [], 'Executed': []}

            grouped_consumptions[period_name][state_label].append(cons)

        # Show all watering periods that the partner has consumptions in
        partner_period_ids = request.env[
            'wua.gravconsumption'].sudo().search(
            [('partner_id', '=', partner.id)]).mapped('wateringperiod_id').ids
        wateringperiods = request.env['wua.wateringperiod'].sudo().search(
            [('id', 'in', partner_period_ids)],
            order='initial_date desc')

        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration', 'liquidation_on_portal')

        values.update({
            'gravconsumptions': gravconsumptions,
            'grouped_consumptions': grouped_consumptions,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/gravconsumptions',
            'wateringperiods': wateringperiods,
            'selected_wateringperiod_id': (
                int(wateringperiod_id) if wateringperiod_id else None),
            'filter_state': filter_state,
            'partner': partner,
            'liquidation_on_portal': liquidation_on_portal,
            'page_name': 'gravconsumptions',
        })
        return request.render(
            'base_wua_portal_gravity_irrigation'
            '.portal_my_gravconsumptions',
            values)
