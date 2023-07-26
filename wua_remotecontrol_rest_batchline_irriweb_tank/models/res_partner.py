# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _remotecontrol_partner_fields_batchline = [
        'partner_code', 'firstname', 'lastname', 'lastname2', 'vat', 'email',
        'tank_permission'
    ]

    html_scheduling_frame = fields.Text(
        string='IrriWEB Scheduling',
        compute='_compute_html_scheduling_frame')

    @api.multi
    def _compute_html_scheduling_frame(self):
        url_ok, url, width, height = self.sudo()._get_url_frame(
            'solicitudcuba')
        for record in self:
            if url_ok:
                regante_param = str(record.partner_code)
                clientidentify_param = self.sudo().env.user.name
                url = url + '&Regante=' + regante_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_scheduling_frame = \
                    '<p style="text-align:center;margin-top:2px;' + \
                    'margin-left:1px;margin-right:1px; overflow: auto;">' + \
                    '<iframe sandbox="allow-scripts allow-forms ' + \
                    'allow-pointer-lock allow-same-origin ' + \
                    'allow-modals" ' + \
                    'id="iframe_tank_scheduling" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="0" height="' + str(height) + '" ' + \
                    'width="' + str(width) + '"' + \
                    '></iframe></p>'
            else:
                record.html_scheduling_frame = ''

    def _get_url_frame(self, type):
        url_ok = False
        url = ''
        width = 0
        height = 0
        php_frame_enabled = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_enabled')
        php_frame_url = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_url')
        url_irriweb = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_batchline')
        url_ok = php_frame_enabled and php_frame_url and url_irriweb
        if url_ok:
            if type == 'solicitudcuba':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_solicitudcuba')
                width = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_solicitudcuba_width')
                height = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_solicitudcuba_height')
            php_frame_client = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_client')
            php_frame_accesskey = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_accesskey')
            php_frame_secretkey = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_secretkey')
            url = php_frame_url + '?type=' + php_frame_type + \
                '&url_irriweb=' + url_irriweb + \
                '&client=' + php_frame_client + \
                '&accesskey=' + php_frame_accesskey + \
                '&secretkey=' + php_frame_secretkey + \
                '&height=' + str(height) + \
                '&width=' + str(width)
        return url_ok, url, width, height

    @api.multi
    def action_scheduling_tank(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Schedule tank'),
            'res_model': 'wizard.scheduling.tank',
            'src_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    # Implemented hook
    def populate_data_for_send_new_partner_batchline(self, vals):
        resp = super(ResPartner, self).\
            populate_data_for_send_new_partner_batchline(vals)
        if (resp):
            tank_permission = not not self.get_val(vals, 'tank_permission')
            resp.update({
                'tank_permission': tank_permission
            })
        return resp

    # Implemented hook
    def send_new_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        try:
            token, error_message = self.get_token(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if token:
                url_send_new_partner = url_remotecontrol_rest + \
                    '/api/regantes'
                headers_data = {
                    'authorization': 'bearer ' + token,
                    'content-type': 'application/json',
                }
                if (not data['vat']):
                    data['vat'] = '-'
                payload_data = {
                    'Identificador': data['partner_code'],
                    'NIF': data['vat'],
                    'Nombre': data['firstname'],
                    'Apellido1': data['lastname'],
                    'Apellido2': data['lastname2'],
                    'Email': data['email'],
                    'PermisoCuba': data['tank_permission'],
                    'DeudaPendiente': False,
                }
                resprest = requests.put(url_send_new_partner,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
                if resprest.status_code == 201:
                    resp = True
                    error_message = ''
                elif resprest.status_code == 200:
                    resp = False
                    error_message = _('User already exists, info updated')
                else:
                    error_message = resprest.text
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    # Implemented hook
    def populate_data_for_update_partner_batchline(self, partner):
        resp = super(ResPartner, self).\
            populate_data_for_update_partner_batchline(partner)
        if resp and partner:
            tank_permission = not not self.refine_value(
                partner.tank_permission)
            resp.update({
                'tank_permission': tank_permission
            })
        return resp

    # Implemented hook
    def update_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        error_message = ''
        try:
            token, error_message = self.get_token(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if token:
                url_send_update_partner = url_remotecontrol_rest + \
                    '/api/regantes'
                headers_data = {
                    'authorization': 'bearer ' + token,
                    'content-type': 'application/json',
                }
                if (not data['vat']):
                    data['vat'] = '-'
                payload_data = {
                    'Identificador': data['partner_code'],
                    'NIF': data['vat'],
                    'Nombre': data['firstname'],
                    'Apellido1': data['lastname'],
                    'Apellido2': data['lastname2'],
                    'Email': data['email'],
                    'PermisoCuba': data['tank_permission'],
                    'DeudaPendiente': data['with_credit_overdue'],
                }
                resprest = requests.put(url_send_update_partner,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
                if resprest.status_code == 200 or resprest.status_code == 201:
                    resp = True
                    error_message = ''
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    # Implemented hook
    def synchronize_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        try:
            token, error_message = self.get_token(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if token:
                url_update_partner = url_remotecontrol_rest + \
                    '/api/regantes/'
                headers_data = {
                    'authorization': 'bearer ' + token,
                    'content-type': 'application/json',
                }
                if (not data['vat']):
                    data['vat'] = '-'
                payload_data = {
                    'Identificador': data['partner_code'],
                    'NIF': data['vat'],
                    'Nombre': data['firstname'],
                    'Apellido1': data['lastname'],
                    'Apellido2': data['lastname2'],
                    'Email': data['email'],
                    'PermisoCuba': data['tank_permission'],
                    'DeudaPendiente': data['with_credit_overdue'],
                }
                resprest = requests.put(url_update_partner,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
                if resprest.status_code == 200 or resprest.status_code == 201:
                    resp = True
                    error_message = ''
                else:
                    resp = False
                    error_message = resprest.text
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    # Implemented hook
    def synchronize_partners_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        partners_ok = []
        partners_not_ok = []
        try:
            token, error_message = self.get_token(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if token:
                url_update_partner = url_remotecontrol_rest + \
                    '/api/regantes/'
                headers_data = {
                    'authorization': 'bearer ' + token,
                    'content-type': 'application/json',
                }
                for data in list_of_data:
                    if (not data['vat']):
                        data['vat'] = '-'
                    payload_data = {
                        'Identificador': data['partner_code'],
                        'NIF': data['vat'],
                        'Nombre': data['firstname'],
                        'Apellido1': data['lastname'],
                        'Apellido2': data['lastname2'],
                        'Email': data['email'],
                        'PermisoCuba': data['tank_permission'],
                        'DeudaPendiente': data['with_credit_overdue'],
                    }
                    resprest = requests.put(url_update_partner,
                                            data=json.dumps(payload_data),
                                            headers=headers_data)
                    if resprest.status_code == 200 or resprest.status_code == \
                            201:
                        partners_ok.append(data['partner_code'])
                    else:
                        partners_not_ok.append(data['partner_code'])
                    pass
        except Exception:
            pass
        return partners_ok, partners_not_ok
