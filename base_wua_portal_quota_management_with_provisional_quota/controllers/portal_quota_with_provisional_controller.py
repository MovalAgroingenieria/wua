# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class PortalQuotaWithProvisional(http.Controller):

    _items_per_page = 10

    @http.route(['/my/quotas', '/my/quotas/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_quotas(self, page=1, search=None,
                         search_field=None, controlperiod_id=None,
                         selected_columns=None, **kw):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }
        env = request.env
        quota_model = env['wua.quota']
        agric_model = env['wua.agriculturalseason']
        current_season = agric_model.search([
            ('active_agriculturalseason', '=', True)], limit=1)
        domain = [
            ('partner_id', '=', partner.id),
            ('quotaperiod_id.is_closed', '=', False),
            '|',
            ('accumulated_input', '!=', 0),
            ('accumulated_consumption', '!=', 0),
        ]
        if current_season:
            domain.insert(1, ('agriculturalseason_id', '=', current_season.id))
        if search and search_field:
            field_map = {
                'period_initial_date': 'quotaperiod_id.initial_date',
                'period_end_date': 'quotaperiod_id.end_date',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        quotas_count = quota_model.search_count(domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/quotas",
            total=quotas_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'controlperiod_id': controlperiod_id,
            },
        )
        offset = (page - 1) * items_per_page
        quotas = quota_model.search(
            domain, limit=items_per_page, offset=offset)
        controlperiod_model = env['wua.controlperiod']
        current_controlperiod = controlperiod_model.search([
            ('state', '=', 'active')], limit=1)
        if not controlperiod_id and current_controlperiod:
            controlperiod_id = current_controlperiod.id
        controlperiods = controlperiod_model.search([])
        values.update({
            'quotas': quotas,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'controlperiods': controlperiods,
            'current_controlperiod': current_controlperiod,
            'selected_controlperiod_id': int(controlperiod_id) if controlperiod_id else None,
            'default_url': '/my/quotas'
        })
        return request.render(
            "base_wua_portal_quota_management.portal_my_quotas",
            values)

    @http.route(['/my/controlconsumptions',
                 '/my/controlconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_controlconsumptions(self, page=1, search=None,
                                      search_field=None, controlperiod_id=None,
                                      **kw):
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner,
        }
        env = request.env
        waterconnection_model = env['res.partner.waterconnection']
        partner_domain = [('partner_id', '=', partner.id)]
        if search and search_field:
            partner_field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
            }
            if search_field in partner_field_map:
                partner_domain.append((partner_field_map[search_field], 'ilike', search))
        partner_links = waterconnection_model.sudo().search(partner_domain)
        waterconnections_ids = partner_links.mapped('waterconnection_id').ids
        current_controlperiod = env['wua.controlperiod'].search([
            ('state', '=', 'active')], limit=1)
        if not controlperiod_id and current_controlperiod:
            controlperiod_id = current_controlperiod.id
        controlpresconsumptions_domain = [
            ('waterconnection_id', 'in', waterconnections_ids)
        ]
        if controlperiod_id:
            controlpresconsumptions_domain.append(
                ('controlperiod_id', '=', int(controlperiod_id)))
        if search and search_field:
            field_map = {
                'waterconnection': 'waterconnection_id.name',
                'watermeter': 'watermeter_id.name',
                'reading_initial_time': 'reading_initial_time',
                'reading_end_time': 'reading_end_time',
            }
            if search_field in field_map:
                controlpresconsumptions_domain.append(
                    (field_map[search_field], 'ilike', search))
        cp_model = env['wua.controlpresconsumption']
        controlpresconsumptions_count = cp_model.search_count(controlpresconsumptions_domain)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/controlconsumptions",
            total=controlpresconsumptions_count,
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
            controlpresconsumptions_domain, limit=items_per_page, offset=offset,
            order='reading_end_time desc')
        controlperiods = env['wua.controlperiod'].search([])
        values.update({
            'controlpresconsumptions': controlpresconsumptions,
            'controlperiods': controlperiods,
            'current_controlperiod': current_controlperiod,
            'selected_controlperiod_id': int(controlperiod_id) if controlperiod_id else None,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/controlconsumptions'
        })
        return request.render(
            "base_wua_portal_quota_management_with_provisional_quota."
            "portal_my_controlconsumptions",
            values)
