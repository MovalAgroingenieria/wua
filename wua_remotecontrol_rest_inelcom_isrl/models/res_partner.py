# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Implemented hook
    def populate_data_for_send_new_partner(self, vals):
        resp = None
        if vals and 'partner_code' in vals:
            partner_code = vals['partner_code']
            firstname = self.get_val(vals, 'firstname')
            lastname = self.get_val(vals, 'lastname')
            lastname2 = self.get_val(vals, 'lastname2')
            if self.get_val(vals, 'is_company'):
                firstname = '-'
            vat = self.get_val(vals, 'vat')
            if len(vat) > 2:
                vat = vat[2:]
            street = self.get_val(vals, 'street')
            city = self.get_val(vals, 'city')
            state = ''
            if vals['state_id']:
                state = self.env['res.country.state'].with_context(
                    lang=self.env.user.partner_id.lang).browse(
                        vals['state_id']).name
            country = ''
            if vals['country_id']:
                country = self.env['res.country'].with_context(
                    lang=self.env.user.partner_id.lang).browse(
                        vals['country_id']).name
            zipcode = self.get_val(vals, 'zip')
            phone = self.get_val(vals, 'phone')
            mobile = self.get_val(vals, 'mobile')
            email = self.get_val(vals, 'email')
            resp = {
                'partner_code': partner_code,
                'firstname': firstname,
                'lastname': lastname,
                'lastname2': lastname2,
                'vat': vat,
                'street': street,
                'city': city,
                'state': state,
                'country': country,
                'zip': zipcode,
                'phone': phone,
                'mobile': mobile,
                'email': email,
                }
        return resp

    # Implemented hook
    def send_new_partner(self, url_remotecontrol_rest,
                         url_remotecontrol_rest_username,
                         url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_send_new_partner = url_remotecontrol_rest + \
                '/regantes/' + str(data['partner_code']) + \
                '?sesion=' + id_session
            payload_data = {
                'nombre': data['firstname'],
                'apellido1': data['lastname'],
                'apellido2': data['lastname2'],
                'nif': data['vat'],
                'direccion': data['street'],
                'localidad': data['city'],
                'municipio': '',
                'provincia': data['state'],
                'pais': data['country'],
                'codPostal': data['zip'],
                'cuentaFact': '',
                'telf1': data['phone'],
                'telf2': data['mobile'],
                'email': data['email'],
                'juntaLocal': '',
                'cooperativa': '',
                'observaciones': _('Origen: Moval Regadío'),
                'factPendientes': '',
                }
            # Provisional
            # print url_send_new_partner
            resprest = requests.post(url_send_new_partner,
                                     data=json.dumps(payload_data),
                                     headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

    # Implemented hook
    def populate_data_for_update_partner(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            firstname = self.refine_value(partner.firstname)
            lastname = self.refine_value(partner.lastname)
            lastname2 = self.refine_value(partner.lastname2)
            if partner.is_company:
                firstname = '-'
            vat = self.refine_value(partner.vat)
            if vat and len(vat) > 2:
                vat = vat[2:]
            street = self.refine_value(partner.street)
            city = self.refine_value(partner.city)
            state = ''
            if partner.state_id:
                state = self.env['res.country.state'].with_context(
                    lang=self.env.user.partner_id.lang).browse(
                        partner.state_id.id).name
            country = ''
            if partner.country_id:
                country = self.env['res.country'].with_context(
                    lang=self.env.user.partner_id.lang).browse(
                        partner.country_id.id).name
            zipcode = self.refine_value(partner.zip)
            phone = self.refine_value(partner.phone)
            mobile = self.refine_value(partner.mobile)
            email = self.refine_value(partner.email)
            acc_number = self.get_bank_account(partner_code)
            resp = {
                'partner_code': partner_code,
                'firstname': firstname,
                'lastname': lastname,
                'lastname2': lastname2,
                'vat': vat,
                'street': street,
                'city': city,
                'state': state,
                'country': country,
                'zip': zipcode,
                'phone': phone,
                'mobile': mobile,
                'email': email,
                'acc_number': acc_number,
                }
        return resp

    # Implemented hook
    def update_partner(self, url_remotecontrol_rest,
                       url_remotecontrol_rest_username,
                       url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_update_partner = url_remotecontrol_rest + \
                '/regantes/' + str(data['partner_code']) + \
                '?sesion=' + id_session
            payload_data = {
                'nuevoNSocio': '',
                'nombre': data['firstname'],
                'apellido1': data['lastname'],
                'apellido2': data['lastname2'],
                'nif': data['vat'],
                'direccion': data['street'],
                'localidad': data['city'],
                'municipio': '',
                'provincia': data['state'],
                'pais': data['country'],
                'codPostal': data['zip'],
                'cuentaFact': data['acc_number'],
                'telf1': data['phone'],
                'telf2': data['mobile'],
                'email': data['email'],
                'juntaLocal': '',
                'cooperativa': '',
                'observaciones': _('Origen: Moval Regadío'),
                'factPendientes': '',
                }
            # Provisional
            # print url_update_partner
            resprest = requests.put(url_update_partner,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            # print resprest.status_code
            # print resprest.text
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

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

    def get_bank_account(self, partner_code):
        resp = ''
        partner = self.env['res.partner'].search(
            [('partner_code', '=', partner_code)])
        if partner:
            partner = partner[0]
            bankaccounts = self.env['res.partner.bank'].search(
                [('partner_id', '=', partner.id)], limit=1)
            if bankaccounts:
                resp = bankaccounts[0].acc_number
        return resp
