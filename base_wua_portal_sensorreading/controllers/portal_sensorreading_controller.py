# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_sensorreadings(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add sensor readings count to main account page """
        response = super(website_sensorreadings, self).account(**kw)
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        sensorreadings = request.env['res.partner.sensor.reading']
        sensorreadings_count = sensorreadings.search_count(
            [('partner_id', '=', partner.id)])
        response.qcontext.update({
            'sensorreadings_count': sensorreadings_count,
        })
        return response

    @http.route(['/my/sensorreadings', '/my/sensorreadings/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_sensorreadings(self, page=1, date_begin=None,
                          date_end=None, search=None, search_field=None,
                          sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner

        sensorreadings_model = request.env['res.partner.sensor.reading']
        domain = [('partner_id', '=', partner.id)]

        if search and search_field:
            search_term = '%%%s%%' % search
            if search_field == 'device_id':
                request.env.cr.execute("""
                    SELECT DISTINCT device_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND device_id IN (
                        SELECT id FROM mdm_measurement_device
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                device_ids = [row[0] for row in request.env.cr.fetchall() if row[0]]
                if device_ids:
                    domain.append(('device_id', 'in', device_ids))
                else:
                    domain.append(('id', '=', False))

            elif search_field == 'sensor_id':
                request.env.cr.execute("""
                    SELECT DISTINCT sensor_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND sensor_id IN (
                        SELECT id FROM mdm_measurement_device_sensor
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                sensor_ids = [row[0] for row in request.env.cr.fetchall() if row[0]]
                if sensor_ids:
                    domain.append(('sensor_id', 'in', sensor_ids))
                else:
                    domain.append(('id', '=', False))

            elif search_field == 'type_id':
                request.env.cr.execute("""
                    SELECT DISTINCT type_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND type_id IN (
                        SELECT id FROM mdm_measurement_device_sensor_type
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                type_ids = [row[0] for row in request.env.cr.fetchall() if row[0]]
                if type_ids:
                    domain.append(('type_id', 'in', type_ids))
                else:
                    domain.append(('id', '=', False))

        # Sorting functionality
        sort_map = {
            'name': 'name asc',
            'measurement_time': 'measurement_time desc',
        }
        order = sort_map.get(sortby, 'name asc')  # Default ordering

        sensorreadings_count = sensorreadings_model.search_count(domain)

        # Pagination
        url_args = {}
        if search:
            url_args['search'] = search
        if search_field:
            url_args['search_field'] = search_field
        if sortby:
            url_args['sortby'] = sortby

        pager = request.website.pager(
            url="/my/sensorreadings",
            total=sensorreadings_count,
            page=page,
            step=self._items_per_page,
            url_args=url_args
        )

        sensorreadings = sensorreadings_model.search(
            domain,
            limit=self._items_per_page,
            offset=pager['offset'],
            order=order
        )

        values.update({
            'sensorreadings': sensorreadings,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'sortby': sortby,
            'default_url': '/my/sensorreadings',
        })
        return request.render(
            "base_wua_portal_sensorreading.portal_my_sensorreadings", values)