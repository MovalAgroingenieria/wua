# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PortalIrrigationMonitoring(http.Controller):

    _items_per_page = 10

    def _prepare_portal_layout_values(self):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        waterconnection = request.env['res.partner.waterconnection']
        waterconnections = waterconnection.search(
            [('partner_id', '=', partner.id)]).mapped('waterconnection_id').ids
        current_controlperiod = request.env['wua.controlperiod'].search(
            [('state', '=', 'active')], limit=1)
        controlreadings_domain = [
            ('waterconnection_id', 'in', waterconnections),
        ]
        if current_controlperiod:
            controlreadings_domain.append(
                ('controlperiod_id', '=', current_controlperiod.id))
        controlreadings_count = request.env['wua.controlreading'].search_count(
            controlreadings_domain)
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner,
            'controlreadings_count': controlreadings_count,
        }
        return values

    @http.route(['/my/controlreadings',
                 '/my/controlreadings/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_controlreadings(self, page=1, search=None,
                                  search_field=None, controlperiod_id=None,
                                  **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        waterconnection = request.env['res.partner.waterconnection']
        partner_domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            partner_field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
            }
            if search_field in partner_field_map:
                partner_domain.append((partner_field_map[search_field],
                                       'ilike', search))
        partner_links = waterconnection.sudo().search(partner_domain)
        waterconnections_ids = partner_links.mapped('waterconnection_id').ids
        waterconnections = request.env['wua.waterconnection'].browse(
            waterconnections_ids)
        parcels = request.env['wua.parcel.partnerlink'].search([
            ('partner_id', '=', partner.id),
        ])
        if parcels:
            parcel_ids = parcels.mapped('parcel_id').ids
            irrigation_points = request.env[
                'wua.parcel.irrigationpoint'].search([
                    ('parcel_id', 'in', parcel_ids),
                    ('type', '=', 'WC'),
                ])
            if irrigation_points:
                _logger.info("Irrigation point waterconnections: %s",
                             irrigation_points.mapped(
                                 'waterconnection_id').ids)
        current_controlperiod = request.env['wua.controlperiod'].search(
            [('state', '=', 'active')], limit=1)
        if not controlperiod_id and current_controlperiod:
            controlperiod_id = current_controlperiod.id
        controlreadings_domain = [
            ('waterconnection_id', 'in', waterconnections_ids),
        ]
        if controlperiod_id:
            controlreadings_domain.append(
                ('controlperiod_id', '=', int(controlperiod_id)))
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
                'reading_time': 'reading_time',
            }
            if search_field in field_map:
                controlreadings_domain.append(
                    (field_map[search_field], 'ilike', search))
        controlreadings_count = request.env['wua.controlreading'].search_count(
            controlreadings_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/controlreadings",
            total=controlreadings_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'controlperiod_id': controlperiod_id,
            },
        )
        offset = (page - 1) * items_per_page
        controlreadings = request.env['wua.controlreading'].search(
            controlreadings_domain, limit=items_per_page, offset=offset,
            order='reading_time desc')
        controlperiods = request.env['wua.controlperiod'].search([])
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'controlreadings': controlreadings,
            'waterconnections': waterconnections,
            'controlperiods': controlperiods,
            'current_controlperiod': current_controlperiod,
            'selected_controlperiod_id': int(controlperiod_id)
            if controlperiod_id else None,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/controlreadings',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_pressurized_irrigation_monitoring."
            "portal_my_controlreadings",
            values)

    @http.route(['/my/controlpresconsumptions',
                 '/my/controlpresconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_controlpresconsumptions(
        self, page=1, search=None, search_field=None, controlperiod_id=None,
            **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        waterconnection = request.env['res.partner.waterconnection']
        partner_domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            partner_field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
            }
            if search_field in partner_field_map:
                partner_domain.append((
                    partner_field_map[search_field], 'ilike', search))
        partner_links = waterconnection.sudo().search(partner_domain)
        waterconnection_ids = partner_links.mapped('waterconnection_id').ids
        current_controlperiod = request.env['wua.controlperiod'].search([
            ('state', '=', 'active')], limit=1)
        if not controlperiod_id and current_controlperiod:
            controlperiod_id = current_controlperiod.id
        cp_domain = [
            ('waterconnection_id', 'in', waterconnection_ids),
        ]
        if controlperiod_id:
            cp_domain.append(('controlperiod_id', '=', int(controlperiod_id)))
        if search and search_field:
            cp_field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
                'reading_initial_time': 'reading_initial_time',
                'reading_end_time': 'reading_end_time',
            }
            if search_field in cp_field_map:
                cp_domain.append((cp_field_map[search_field], 'ilike', search))
        cp_model = request.env['wua.controlpresconsumption']
        cp_count = cp_model.search_count(cp_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/controlpresconsumptions",
            total=cp_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'controlperiod_id': controlperiod_id,
            },
        )
        offset = (page - 1) * items_per_page
        controlpresconsumptions = cp_model.search(
            cp_domain, limit=items_per_page, offset=offset,
            order='reading_end_time desc')
        controlperiods = request.env['wua.controlperiod'].search([])
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'controlpresconsumptions': controlpresconsumptions,
            'controlperiods': controlperiods,
            'current_controlperiod': current_controlperiod,
            'selected_controlperiod_id': int(controlperiod_id)
            if controlperiod_id else None,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/controlpresconsumptions',
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_pressurized_irrigation_monitoring."
            "portal_my_controlpresconsumptions",
            values)
