# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import urllib

import werkzeug.exceptions
import werkzeug.utils

from odoo import http
from odoo.http import request
from odoo.addons.base_wua_portal_sensorreading.controllers.\
    portal_sensorreading_controller import website_sensorreadings


class website_sensorreadings_grafana(website_sensorreadings):

    GRAFANA_ROUTE = "/my/sensorreadings/grafana"
    GRAFANA_VIEWS = ("grafana", "grafana-histogram")

    def _get_grafana_dashboard(self, view):
        if view == "grafana-histogram":
            setting = "portal_user_sensorreading_dashboard_histogram_id"
        else:
            setting = "portal_user_sensorreading_dashboard_id"
        dashboard_id = request.env["ir.values"].get_default(
            "mdm.config.settings", setting)
        return request.env[
            "board.grafana.dashboard.storage"].sudo().browse(dashboard_id)

    def _get_grafana_datasource(self):
        grafana_default_datasource = request.env["ir.values"].get_default(
            "board.grafana.configuration", "grafana_default_datasource")
        return grafana_default_datasource or request.env.cr.dbname

    def _get_grafana_dashboard_path(self, view):
        # Built on the server from the partner of the session: the portal
        # user can not choose the parameters of the dashboard
        dashboard = self._get_grafana_dashboard(view)
        if not dashboard.dashboard_path:
            return False
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        path = dashboard.dashboard_path
        path += "&var-datasource=" + self._get_grafana_datasource()
        path += "&var-partner_id=" + str(partner.id)
        # Limit type of sensors
        request.env.cr.execute("""
            SELECT DISTINCT type_id
            FROM res_partner_sensor_reading
            WHERE partner_id = %s;""", (partner.id,))
        for row in request.env.cr.fetchall():
            if row[0]:
                path += "&var-sensor_type_ids=" + str(row[0])
        return path

    def get_grafana_dashboard_configuration(self, view):
        dashboard = self._get_grafana_dashboard(view)
        db_name = self._get_grafana_datasource()
        grafana_model = request.env["board.grafana"].sudo()
        frame_url = False
        if dashboard.dashboard_path and grafana_model._get_grafana_url():
            # Loaded through Odoo, which signs the portal user in to Grafana
            frame_url = "%s?%s" % (
                self.GRAFANA_ROUTE, urllib.urlencode({"view": view}))
        frame_width = dashboard.frame_width or "100%"
        frame_height = dashboard.frame_height or "600px"
        return db_name, frame_url, frame_width, frame_height

    @http.route(GRAFANA_ROUTE, type="http", auth="user", website=True)
    def portal_my_sensorreadings_grafana(self, view=None, **kw):
        if view not in self.GRAFANA_VIEWS:
            raise werkzeug.exceptions.NotFound()
        path = self._get_grafana_dashboard_path(view)
        url = False
        if path:
            url = request.env["board.grafana"].sudo()._get_grafana_signed_url(
                path)
        if not url:
            raise werkzeug.exceptions.NotFound()
        response = werkzeug.utils.redirect(url, 303)
        response.headers["Cache-Control"] = "no-store"
        return response

    @http.route(["/my/sensorreadings", "/my/sensorreadings/page/<int:page>"],
                type="http", auth="user", website=True)
    def portal_my_sensorreadings(
            self, page=1, date_begin=None,
            date_end=None, search=None, search_field=None,
            sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        view = kw.get('view', 'grafana')
        sensorreadings_model = request.env["res.partner.sensor.reading"]
        domain = [("partner_id", "=", partner.id)]
        if search and search_field:
            search_term = "%%%s%%" % search
            if search_field == "device_id":
                request.env.cr.execute("""
                    SELECT DISTINCT device_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND device_id IN (
                        SELECT id FROM mdm_measurement_device
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                device_ids = \
                    [row[0] for row in request.env.cr.fetchall() if row[0]]
                if device_ids:
                    domain.append(("device_id", "in", device_ids))
                else:
                    domain.append(("id", "=", False))
            elif search_field == "sensor_id":
                request.env.cr.execute("""
                    SELECT DISTINCT sensor_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND sensor_id IN (
                        SELECT id FROM mdm_measurement_device_sensor
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                sensor_ids = \
                    [row[0] for row in request.env.cr.fetchall() if row[0]]
                if sensor_ids:
                    domain.append(("sensor_id", "in", sensor_ids))
                else:
                    domain.append(("id", "=", False))
            elif search_field == "type_id":
                request.env.cr.execute("""
                    SELECT DISTINCT type_id
                    FROM res_partner_sensor_reading
                    WHERE partner_id = %s
                    AND type_id IN (
                        SELECT id FROM mdm_measurement_device_sensor_type
                        WHERE name ILIKE %s
                    )
                """, (partner.id, search_term))
                type_ids = \
                    [row[0] for row in request.env.cr.fetchall() if row[0]]
                if type_ids:
                    domain.append(("type_id", "in", type_ids))
                else:
                    domain.append(("id", "=", False))
        # Sorting functionality
        sort_map = {
            "name": "name asc",
            "measurement_time": "measurement_time desc",
        }
        order = sort_map.get(sortby, "name asc")  # Default ordering
        sensorreadings_count = sensorreadings_model.search_count(domain)
        # Pagination
        url_args = {}
        if search:
            url_args["search"] = search
        if search_field:
            url_args["search_field"] = search_field
        if sortby:
            url_args["sortby"] = sortby
        pager = request.website.pager(
            url="/my/sensorreadings",
            total=sensorreadings_count,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        sensorreadings = sensorreadings_model.search(
            domain,
            limit=self._items_per_page,
            offset=pager["offset"],
            order=order,
        )
        values.update({
            "sensorreadings": sensorreadings,
            "pager": pager,
            "search_query": search,
            "search_field": search_field,
            "sortby": sortby,
            "default_url": "/my/sensorreadings",
            "view": view,
        })
        # Grafana views
        frame_id = "portal_user_sensorreading_grafana"
        db_name, frame_url, frame_width, frame_height = \
            self.get_grafana_dashboard_configuration(view)
        # Set frame values
        values.update({
            "frame_id": frame_id,
            "frame_url": frame_url,
            "frame_width": frame_width,
            "frame_height": frame_height,
        })
        # Render template with Grafana extensions
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'view': view,
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            "base_wua_portal_sensorreading.portal_my_sensorreadings", values)
