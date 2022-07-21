# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _remotecontrol_partner_fields_batchline = [
        'partner_code', 'firstname', 'lastname', 'lastname2', 'vat', 'email'
    ]

    def get_token(self, url_remotecontrol_rest,
                  url_remotecontrol_rest_username,
                  url_remotecontrol_rest_password):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/token'
        auth_data = {
            'username': url_remotecontrol_rest_username,
            'password': url_remotecontrol_rest_password,
            'grant_type': 'password',
        }
        headers_data = {
            'content-type': 'application/json',
        }
        resprest = requests.post(url_open_session,
                                 data=auth_data,
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            outputrest = json.loads(resprest.text)
            resp = outputrest['access_token']
        return resp, error_message

    # Implemented hook
    def populate_data_for_send_new_partner_batchline(self, vals):
        resp = None
        if vals and 'partner_code' in vals:
            partner_code = vals['partner_code']
            is_company = self.get_val(vals, 'company_type') == 'company'
            if (is_company):
                firstname = self.get_val(vals, 'lastname')
                lastname = ''
                lastname2 = ''
            else:
                firstname = self.get_val(vals, 'firstname')
                lastname = self.get_val(vals, 'lastname')
                lastname2 = self.get_val(vals, 'lastname2')
            vat = self.get_val(vals, 'vat')
            if not vat:
                vat = '-'
            elif len(vat) > 2:
                vat = vat[2:]
            email = self.get_val(vals, 'email')
            resp = {
                'partner_code': partner_code,
                'firstname': firstname,
                'lastname': lastname,
                'lastname2': lastname2,
                'vat': vat,
                'email': email,
                }
        return resp

    # Implemented hook
    def send_new_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
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
        return resp, error_message

    def send_partner_on_creation_telecontrol(self, new_partner, vals):
        super(ResPartner, self).send_partner_on_creation_telecontrol(
            new_partner, vals
        )
        self.send_partner_on_creation('batchline', new_partner, vals)

    # Implemented hook
    def populate_data_for_update_partner_batchline(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            if (partner.is_company):
                firstname = self.refine_value(partner.name)
            else:
                firstname = self.refine_value(partner.firstname)
            lastname = self.refine_value(partner.lastname)
            lastname2 = self.refine_value(partner.lastname2)
            vat = self.refine_value(partner.vat)
            if vat and len(vat) > 2:
                vat = vat[2:]
            else:
                vat = '-'
            email = self.refine_value(partner.email)
            with_credit_overdue = partner.credit_overdue > 0
            resp = {
                'partner_code': partner_code,
                'firstname': firstname,
                'lastname': lastname,
                'lastname2': lastname2,
                'vat': vat,
                'email': email,
                'with_credit_overdue': with_credit_overdue,
                }
        return resp

    # Implemented hook
    def update_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        error_message = ''
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
                'DeudaPendiente': data['with_credit_overdue'],
            }
            resprest = requests.put(url_send_update_partner,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            if resprest.status_code == 200 or resprest.status_code == 201:
                resp = True
                error_message = ''
        return resp, error_message

    def send_partner_on_write_telecontrol(self, vals):
        super(ResPartner, self).send_partner_on_write_telecontrol(vals)
        self.send_partner_on_write('batchline', vals)

    # Implemented hook
    def populate_data_for_delete_partner_batchline(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            resp = {
                'partner_code': partner_code,
                }
        return resp

    # Implemented hook
    def delete_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_remove_partner = url_remotecontrol_rest + \
                '/api/regantes/' + str(data['partner_code'])
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.delete(url_remove_partner,
                                       headers=headers_data)
            if resprest.status_code == 200:
                resp = True
                error_message = ''
            else:
                resp = False
                error_message = resprest.text
        return resp, error_message

    def unlink_partner_on_unlink_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unlink_telecontrol()
        self.unlink_partner_on_unlink('batchline')

    # Implemented hook
    def synchronize_partner_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
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
        return resp, error_message

    def create_partner_on_synchronize_telecontrol(self):
        super(ResPartner, self).create_partner_on_synchronize_telecontrol()
        self.create_partner_on_syncrhonize('batchline')

    # Implemented hook
    def synchronize_partners_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        partners_ok = []
        partners_not_ok = []
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
                    'DeudaPendiente': data['with_credit_overdue'],
                }
                resprest = requests.put(url_update_partner,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
                if resprest.status_code == 200 or resprest.status_code == 201:
                    partners_ok.append(data['partner_code'])
                else:
                    partners_not_ok.append(data['partner_code'])
                pass
        return partners_ok, partners_not_ok

    def create_partners_on_synchronize_telecontrol(self, active_partners):
        super(ResPartner, self).create_partners_on_synchronize_telecontrol(
            active_partners)
        self.create_partners_on_synchronize(active_partners, 'batchline')

    def unlink_partner_on_unsynchronize_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unsynchronize_telecontrol()
        self.unlink_partner_on_unsyncrhonize('batchline')

    def get_val(self, vals, key):
        resp = ''
        if vals[key]:
            resp = vals[key]
        return resp

    def refine_value(self, value):
        resp = ''
        if value:
            resp = value
        return resp


class ResPartnerWaterconnection(models.Model):
    _inherit = 'res.partner.waterconnection'

    html_readings_url = fields.Text(
        string='IrriWEB Readings',
        compute='_compute_html_readings_url'
        )

    html_consumptions_url = fields.Text(
        string='IrriWEB Consumptions',
        compute='_compute_html_consumptions_url'
        )

    html_scheduling_url = fields.Text(
        string='IrriWEB Scheduling',
        compute='_compute_html_scheduling_url'
        )

    @api.multi
    def _compute_html_readings_url(self):
        url_ok, url = self.sudo()._get_url_frame_info('historico')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().waterconnection_id.\
                    irrigationshed_id.name
                toma_param = str(record.sudo().waterconnection_id.position)
                clientidentify_param = self.sudo().env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_readings_url = url
            else:
                record.html_readings_url = ''

    @api.multi
    def _compute_html_consumptions_url(self):
        url_ok, url = self.sudo()._get_url_frame_info('consumo')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().waterconnection_id.\
                    irrigationshed_id.name
                toma_param = str(record.sudo().waterconnection_id.position)
                clientidentify_param = self.sudo().env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_consumptions_url = url
            else:
                record.html_consumptions_url = ''

    @api.multi
    def _compute_html_scheduling_url(self):
        url_ok, url = self.sudo()._get_url_frame_info('programacion')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().waterconnection_id.\
                    irrigationshed_id.name
                toma_param = str(record.sudo().waterconnection_id.position)
                clientidentify_param = self.sudo().env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_scheduling_url = url
            else:
                record.html_scheduling_url = ''

    def _get_url_frame_info(self, type):
        url_ok = False
        url = ''
        php_frame_enabled = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_enabled')
        php_frame_url = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_url')
        url_irriweb = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_application')
        url_ok = php_frame_enabled and php_frame_url and url_irriweb
        if url_ok:
            if type == 'historico':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_historico')
            if type == 'consumo':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_consumo')
            if type == 'programacion':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_programacion')
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
                '&secretkey=' + php_frame_secretkey
        return url_ok, url

    @api.multi
    def action_see_readings(self):
        self.ensure_one()
        if self.html_readings_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.html_readings_url,
                'target': 'new',
            }

    @api.multi
    def action_see_consumptions(self):
        self.ensure_one()
        if self.html_readings_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.html_consumptions_url,
                'target': 'new',
            }

    @api.multi
    def action_see_scheduling(self):
        self.ensure_one()
        if self.html_readings_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.html_scheduling_url,
                'target': 'new',
            }
