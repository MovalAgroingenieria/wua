# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo import _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 20

    def _get_portal_partner(self):
        partner = request.env.user.partner_id
        return partner.parent_id or partner

    def _get_portal_wateringperiod_domain(self, partner):
        return [('state', '=', 'open')]

    def _get_portal_subparcel_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
            ('irrigationgate_id', '!=', False),
            ('parcel_id.gravityfed_irrigation_right', '=', True),
            ('parcel_id.with_watering_shift', '=', True),
        ]

    def _get_portal_watering_product_domain(self, partner):
        wateringrequest = request.env['wua.wateringrequest'].sudo().new({
            'partner_id': partner.id,
        })
        product_domain = [('categ_id.productcategory_code', '=', 8)]
        if hasattr(wateringrequest, 'get_domain_product_id'):
            product_domain = wateringrequest.get_domain_product_id()
        return product_domain

    @http.route()
    def account(self, **kw):
        """Add gravity irrigation consumptions count to main account page"""
        response = super(website_account, self).account(**kw)
        partner = self._get_portal_partner()

        gravconsumption_count = request.env[
            'wua.gravconsumption'].sudo().search_count(
            [('partner_id', '=', partner.id)])
        wateringrequest_count = request.env[
            'wua.wateringrequest'].sudo().search_count(
            [('partner_id', '=', partner.id)])

        response.qcontext.update({
            'gravconsumption_count': gravconsumption_count,
            'wateringrequest_count': wateringrequest_count,
        })
        return response

    @http.route(['/my/wateringrequests',
                 '/my/wateringrequests/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_wateringrequests(self, page=1, search=None,
                                   search_field=None,
                                   wateringperiod_id=None,
                                   filter_is_open=None,
                                   success=None,
                                   error=None, **kw):
        """Portal view for gravity irrigation requests."""
        values = self._prepare_portal_layout_values()
        partner = self._get_portal_partner()

        domain = [('partner_id', '=', partner.id)]

        if wateringperiod_id:
            try:
                domain.append(
                    ('wateringperiod_id', '=', int(wateringperiod_id)))
            except (TypeError, ValueError):
                pass

        if filter_is_open in ('open', 'closed'):
            domain.append(('is_open', '=', filter_is_open == 'open'))

        if search and search_field:
            field_map = {
                'name': 'name',
                'request_date': 'request_date',
                'state': 'state',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        wateringrequest_model = request.env['wua.wateringrequest'].sudo()
        wateringrequest_count = wateringrequest_model.search_count(domain)

        pager = request.website.pager(
            url='/my/wateringrequests',
            total=wateringrequest_count,
            page=page,
            step=self._items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
                'wateringperiod_id': wateringperiod_id,
                'filter_is_open': filter_is_open,
            },
        )

        wateringrequests = wateringrequest_model.search(
            domain,
            limit=self._items_per_page,
            offset=pager['offset'],
            order='wateringperiod_id desc, is_open desc, request_date desc',
        )

        grouped_requests = {}
        for req in wateringrequests:
            period_name = (
                req.wateringperiod_id.display_name
                if req.wateringperiod_id else 'No Period'
            )
            status = 'Open' if req.is_open else 'Closed'
            if period_name not in grouped_requests:
                grouped_requests[period_name] = {'Open': [], 'Closed': []}
            grouped_requests[period_name][status].append(req)

        wateringperiod_domain = self._get_portal_wateringperiod_domain(
            partner)
        wateringperiods = request.env['wua.wateringperiod'].sudo().search(
            wateringperiod_domain,
            order='initial_date desc')
        subparcel_domain = self._get_portal_subparcel_domain(partner)
        subparcels = request.env['wua.parcel.subparcel'].sudo().search(
            subparcel_domain,
            order='subparcel_code')
        product_domain = self._get_portal_watering_product_domain(partner)
        products = request.env['product.product'].sudo().search(
            product_domain,
            order='name')

        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration', 'liquidation_on_portal')

        values.update({
            'wateringrequests': wateringrequests,
            'grouped_requests': grouped_requests,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/wateringrequests',
            'wateringperiods': wateringperiods,
            'selected_wateringperiod_id': (
                int(wateringperiod_id) if wateringperiod_id else None),
            'filter_is_open': filter_is_open,
            'success_message': success,
            'error_message': error,
            'subparcels': subparcels,
            'watering_products': products,
            'partner': partner,
            'liquidation_on_portal': liquidation_on_portal,
            'page_name': 'wateringrequests',
        })
        return request.render(
            'base_wua_portal_gravity_irrigation.portal_my_wateringrequests',
            values)

    @http.route('/my/wateringrequest/request', type='json', auth='user',
                methods=['POST'])
    def portal_create_wateringrequest(self, wateringperiod_id=None,
                                      product_id=None, lines=None,
                                      notes=None, **post):
        """Create a gravity irrigation request from the portal (JSON).

        Expected params:
            wateringperiod_id (int)
            product_id (int)
            lines (list of dicts): [{'subparcel_id': int,
                                     'watering_hours': float}, ...]
            notes (str, optional)
        """
        result = {
            'success': False,
            'message': '',
            'wateringrequest_id': False,
        }
        partner = self._get_portal_partner()
        notes = (notes or '').strip()
        error = ''
        wateringperiod = None
        product = None
        gravconsumption_vals = []

        try:
            wateringperiod_id = int(wateringperiod_id)
        except (TypeError, ValueError):
            error = _('Invalid watering period.')

        if not error:
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                error = _('Invalid water type.')

        if not error:
            wateringperiod_domain = \
                self._get_portal_wateringperiod_domain(partner)
            wateringperiod = request.env['wua.wateringperiod'].sudo().search(
                [('id', '=', wateringperiod_id)] + wateringperiod_domain,
                limit=1)
            if not wateringperiod:
                error = _('The selected watering period is not valid.')

        if not error:
            existing_wateringrequest = request.env[
                'wua.wateringrequest'].sudo().search([
                    ('partner_id', '=', partner.id),
                    ('wateringperiod_id', '=', wateringperiod.id),
                ], limit=1)
            if existing_wateringrequest:
                error = _('There is already a watering request for this '
                          'period.')

        if not error:
            product_domain = \
                self._get_portal_watering_product_domain(partner)
            product = request.env['product.product'].sudo().search(
                [('id', '=', product_id)] + product_domain, limit=1)
            if not product:
                error = _('The selected water type is not valid.')

        if not error:
            gravconsumption_vals, error = \
                self._prepare_portal_gravconsumption_vals(partner, lines)

        if not error:
            vals = {
                'wateringperiod_id': wateringperiod.id,
                'partner_id': partner.id,
                'product_id': product.id,
                'gravconsumption_ids': gravconsumption_vals,
            }
            if notes:
                vals['notes'] = '<p>%s</p>' % notes
            try:
                wateringrequest = request.env[
                    'wua.wateringrequest'].create(vals)
                result.update({
                    'success': True,
                    'message': _('Watering request created successfully.'),
                    'wateringrequest_id': wateringrequest.id,
                })
            except (AccessError, UserError, ValidationError) as create_error:
                error = create_error.name

        if not result['success']:
            result['message'] = error
        return result

    def _prepare_portal_gravconsumption_vals(self, partner, lines):
        """Validate portal request lines and build gravconsumption commands.

        Returns a tuple (gravconsumption_vals, error). When error is a
        non-empty string, gravconsumption_vals is an empty list.
        """
        gravconsumption_vals = []
        error = ''
        subparcel_domain = self._get_portal_subparcel_domain(partner)
        used_subparcel_ids = set()

        if not lines or not isinstance(lines, (list, tuple)):
            error = _('You must add at least one request line.')

        for line in (lines or []):
            if error:
                break
            if not isinstance(line, dict):
                error = _('Invalid request line.')
                break

            try:
                subparcel_id = int(line.get('subparcel_id'))
            except (TypeError, ValueError):
                error = _('Invalid subparcel.')
                break

            if subparcel_id in used_subparcel_ids:
                error = _('The same subparcel cannot be added more than '
                          'once. Please remove duplicated lines.')
                break
            used_subparcel_ids.add(subparcel_id)

            try:
                watering_hours_value = float(
                    str(line.get('watering_hours')).replace(',', '.'))
            except (TypeError, ValueError):
                error = _('Invalid watering hours.')
                break

            if watering_hours_value <= 0:
                error = _('Watering hours must be greater than 0.')
                break

            half_hours = watering_hours_value * 2.0
            if abs(half_hours - round(half_hours)) > 0.000001:
                error = _('Watering hours must be in 0.5 steps '
                          '(for example: 1, 1.5, 2).')
                break

            watering_duration = int(round(watering_hours_value * 60.0))
            if watering_duration <= 0:
                error = _('Watering duration must be greater than 0.')
                break

            subparcel = request.env['wua.parcel.subparcel'].sudo().search(
                [('id', '=', subparcel_id)] + subparcel_domain, limit=1)
            if not subparcel:
                error = _('The selected subparcel is not valid.')
                break

            gravconsumption_vals.append((0, 0, {
                'subparcel_id': subparcel.id,
                'watering_duration': watering_duration,
                'watering_duration_dechours': watering_hours_value,
            }))

        if error:
            gravconsumption_vals = []
        return gravconsumption_vals, error

    @http.route(['/my/gravconsumptions',
                 '/my/gravconsumptions/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_gravconsumptions(self, page=1, search=None,
                                   search_field=None,
                                   wateringperiod_id=None,
                                   filter_state=None, **kw):
        """Portal view for gravity irrigation consumptions"""
        values = self._prepare_portal_layout_values()
        partner = self._get_portal_partner()

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
