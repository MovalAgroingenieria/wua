# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from datetime import timedelta


class WuaPresreswateringperiod(models.Model):
    _inherit = 'wua.preswateringperiod'

    proration = fields.Float(
        string="Proration",
        required=True,
        digits=(32, 2),
        default=1.0,
    )

    zones_united = fields.Boolean(
        string='Zones United',
        default=False,
    )

    rebombed_flow_ls = fields.Float(
        string='Rebombed Flow (l/s)',
        digits=(32, 0),
        default=0.0,
    )

    by_gravity_outlet = fields.Boolean(
        string='By Gravity Outlet',
        default=False,
    )

    by_pumping = fields.Boolean(
        string='By Pumping',
        default=False,
    )

    by_surplus = fields.Boolean(
        string='By Surplus',
        default=False,
    )

    _sql_constraints = [
        ('check_proration_positive',
         'CHECK(proration > 0)',
         'The value of \'Proration\' must be greater than 0.'),
    ]

    def send_octroi_notifications(self, octroi):
        octroi_consumptions = []
        # Get tomorrow date
        today = fields.Date.from_string(fields.Date.today())
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        today_str = today.strftime('%d-%m-%Y')
        tomorrow_str = tomorrow.strftime('%d-%m-%Y')
        yesterday_str = yesterday.strftime('%d-%m-%Y')
        octroi_requests = self.env['wua.preswateringrequest'].search(
            [('partner_id.octroi_id', '=', octroi.id),
             ('initial_date', '=', tomorrow)])
        for request in octroi_requests:
            partner_id = request.partner_id.id
            previous_request = self.env['wua.preswateringrequest'].search([
                ('partner_id', '=', partner_id),
                ('initial_date', '=', yesterday),
            ], limit=1)
            today_request = self.env['wua.preswateringrequest'].search([
                ('partner_id', '=', partner_id),
                ('initial_date', '=', today),
            ], limit=1)
            for consumption in request.presresconsumption_ids:
                nominal_flow_ls_issued = 0.0
                modified = False
                if previous_request:
                    previous_consumption = previous_request.\
                        presresconsumption_ids.filtered(
                            lambda c: c.waterconnection_id.id ==
                            consumption.waterconnection_id.id)
                    if previous_consumption:
                        nominal_flow_ls_issued = previous_consumption[0].\
                            nominal_flow_ls_issued or 0.0
                if today_request:
                    today_consumption = today_request.presresconsumption_ids.\
                        filtered(lambda c: c.waterconnection_id.id ==
                                 consumption.waterconnection_id.id)
                    if today_consumption:
                        today_nominal_flow = today_consumption[0].\
                            nominal_flow_ls or 0.0
                        if today_nominal_flow != consumption.nominal_flow_ls:
                            modified = True
                octroi_consumptions.append({
                    'water_connection': consumption.waterconnection_id.name,
                    'total_affected_area_official_hec':
                        consumption.total_affected_area_official_hec,
                    'nominal_flow_ls': consumption.nominal_flow_ls,
                    'nominal_flow_ls_issued': nominal_flow_ls_issued,
                    'modified': modified,
                    'partner_code': request.partner_id.partner_code,
                    'partner_name': request.partner_id.display_name,
                })
        if (octroi_consumptions):
            mail_template = self.env.ref(
                'base_wua_cayc_general.'
                'wua_preswatering_octroi_email_template')
            mail_template.with_context({
                'data': {'consumptions': octroi_consumptions},
                'today_str': today_str,
                'tomorrow_str': tomorrow_str,
                'yesterday_str': yesterday_str,
            }).send_mail(octroi.id, force_send=True)

    @api.model
    def send_octroi_notifications_cron_action(self, days_advance=1):
        octrois = self.env['wua.octroi'].search(
            [('responsible_person_id', '!=', False)])
        for octroi in octrois:
            self.send_octroi_notifications(octroi)

    def send_parent_partner_notifications(self):
        parent_consumptions_map = {}
        today = fields.Date.from_string(fields.Date.today())
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        today_str = today.strftime('%d-%m-%Y')
        tomorrow_str = tomorrow.strftime('%d-%m-%Y')
        yesterday_str = yesterday.strftime('%d-%m-%Y')
        tomorrow_requests_children = self.env[
            'wua.preswateringrequest'].search([
                ('partner_id.parent_partner_id', '!=', False),
                ('initial_date', '=', tomorrow),
            ])
        tomorrow_requests_parents = self.env[
            'wua.preswateringrequest'].search([
                ('partner_id.parent_partner_id', '=', False),
                ('initial_date', '=', tomorrow),
            ])
        for request in tomorrow_requests_children:
            parent = request.partner_id.parent_partner_id
            parent_id = parent.id
            parent_consumptions_map.setdefault(parent_id, [])
            for consumption in request.presresconsumption_ids:
                nominal_flow_ls_issued = 0.0
                modified = False

                previous_request = self.env['wua.preswateringrequest'].search([
                    ('partner_id', '=', request.partner_id.id),
                    ('initial_date', '=', yesterday),
                ], limit=1)
                if previous_request:
                    previous_consumption = previous_request.\
                        presresconsumption_ids.filtered(
                            lambda c: c.waterconnection_id.id ==
                            consumption.waterconnection_id.id)
                    if previous_consumption:
                        nominal_flow_ls_issued = previous_consumption[0].\
                            nominal_flow_ls_issued or 0.0
                today_request = self.env['wua.preswateringrequest'].search([
                    ('partner_id', '=', request.partner_id.id),
                    ('initial_date', '=', today),
                ], limit=1)
                if today_request:
                    today_consumption = today_request.presresconsumption_ids.\
                        filtered(lambda c: c.waterconnection_id.id ==
                                 consumption.waterconnection_id.id)
                    if today_consumption:
                        today_nominal_flow = today_consumption[0].\
                            nominal_flow_ls or 0.0
                        if today_nominal_flow != consumption.nominal_flow_ls:
                            modified = True
                parent_consumptions_map[parent_id].append({
                    'water_connection': consumption.waterconnection_id.name,
                    'total_affected_area_official_hec':
                        consumption.total_affected_area_official_hec,
                    'nominal_flow_ls': consumption.nominal_flow_ls,
                    'nominal_flow_issued_ls': nominal_flow_ls_issued,
                    'modified': modified,
                    'partner_code': request.partner_id.partner_code,
                    'partner_name': request.partner_id.display_name,
                })
        for request in tomorrow_requests_parents:
            parent_id = request.partner_id.id
            parent_consumptions_map.setdefault(parent_id, [])
            for consumption in request.presresconsumption_ids:
                nominal_flow_ls_issued = 0.0
                modified = False
                previous_request = self.env['wua.preswateringrequest'].search([
                    ('partner_id', '=', request.partner_id.id),
                    ('initial_date', '=', yesterday),
                ], limit=1)
                if previous_request:
                    previous_consumption = previous_request.\
                        presresconsumption_ids.filtered(
                            lambda c: c.waterconnection_id.id ==
                            consumption.waterconnection_id.id)
                    if previous_consumption:
                        nominal_flow_ls_issued = previous_consumption[0].\
                            nominal_flow_ls_issued or 0.0
                today_request = self.env['wua.preswateringrequest'].search([
                    ('partner_id', '=', request.partner_id.id),
                    ('initial_date', '=', today),
                ], limit=1)
                if today_request:
                    today_consumption = today_request.presresconsumption_ids.\
                        filtered(lambda c: c.waterconnection_id.id ==
                                 consumption.waterconnection_id.id)
                    if today_consumption:
                        today_nominal_flow = today_consumption[0].\
                            nominal_flow_ls or 0.0
                        if today_nominal_flow != consumption.nominal_flow_ls:
                            modified = True
                parent_consumptions_map[parent_id].append({
                    'water_connection': consumption.waterconnection_id.name,
                    'total_affected_area_official_hec':
                        consumption.total_affected_area_official_hec,
                    'nominal_flow_ls': consumption.nominal_flow_ls,
                    'nominal_flow_issued_ls': nominal_flow_ls_issued,
                    'modified': modified,
                    'partner_code': request.partner_id.partner_code,
                    'partner_name': request.partner_id.display_name,
                })
        for parent_id, consumptions in parent_consumptions_map.items():
            parent_partner = self.env['res.partner'].browse(parent_id)
            if parent_partner.email and consumptions:
                mail_template = self.env.ref(
                    'base_wua_cayc_general.'
                    'wua_preswatering_parent_partner_email_template')
                mail_template.with_context({
                    'data': {'consumptions': consumptions},
                    'today_str': today_str,
                    'tomorrow_str': tomorrow_str,
                    'yesterday_str': yesterday_str,
                }).send_mail(parent_partner.id, force_send=True)

    @api.model
    def send_parent_partner_notifications_cron_action(self, days_advance=1):
        self.send_parent_partner_notifications()
