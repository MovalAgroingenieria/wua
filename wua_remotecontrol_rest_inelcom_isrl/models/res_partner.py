# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _remotecontrol_partner_fields_inelcom = [
        'partner_code', 'firstname', 'lastname', 'lastname2', 'vat', 'email',
        'street', 'city', 'state', 'country', 'zip', 'phone', 'mobile'
    ]
    REQUEST_TIMEOUT = 20

    # Implemented hook
    def populate_data_for_send_new_partner_inelcom(self, vals):
        resp = None
        if vals and 'partner_code' in vals:
            partner_code = vals['partner_code']
            firstname = self.get_val(vals, 'firstname')
            lastname = self.get_val(vals, 'lastname')
            lastname2 = self.get_val(vals, 'lastname2')
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
    def send_new_partner_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
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
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data,
                                     timeout=self.REQUEST_TIMEOUT)
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
                    'observaciones': _('Source: Moval Regadío'),
                    'factPendientes': 'NO',
                    }
                resprest = requests.post(url_send_new_partner,
                                         data=json.dumps(payload_data),
                                         headers=headers_data,
                                         timeout=self.REQUEST_TIMEOUT)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    resp = outputrest['resultado'] == 'OK'
                    if not resp:
                        error_message = outputrest['detalleError']
                url_close_session = url_remotecontrol_rest + \
                    '/sesiones/' + id_session
                resprest = requests.delete(url_close_session)
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    def send_partner_on_creation_telecontrol(self, new_partner, vals):
        super(ResPartner, self).send_partner_on_creation_telecontrol(
            new_partner, vals
        )
        self.send_partner_on_creation('inelcom', new_partner, vals)

    # Implemented hook
    def populate_data_for_update_partner_inelcom(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            firstname = self.refine_value(partner.firstname)
            lastname = self.refine_value(partner.lastname)
            lastname2 = self.refine_value(partner.lastname2)
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
            with_credit_overdue = partner.credit_overdue > 0
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
                'with_credit_overdue': with_credit_overdue,
                }
        return resp

    # Implemented hook
    def update_partner_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        error_message = ''
        observ = _('Source: Moval Regadío')
        observ_archived_preffix = _('Archived Data')
        if record_archived:
            observ = observ_archived_preffix + '. ' + observ
        pending_inv = 'NO'
        if data['with_credit_overdue']:
            pending_inv = 'SI'
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data,
                                     timeout=self.REQUEST_TIMEOUT)
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
                    'observaciones': observ,
                    'factPendientes': pending_inv,
                    }
                resprest = requests.put(url_update_partner,
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
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    def send_partner_on_write_telecontrol(self, vals):
        super(ResPartner, self).send_partner_on_write_telecontrol(vals)
        self.send_partner_on_write('inelcom', vals)

    # Implemented hook
    def populate_data_for_delete_partner_inelcom(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            resp = {
                'partner_code': partner_code,
                }
        return resp

    # Implemented hook
    def delete_partner_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
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
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data,
                                     timeout=self.REQUEST_TIMEOUT)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                url_delete_partner = url_remotecontrol_rest + \
                    '/regantes/' + str(data['partner_code']) + \
                    '?sesion=' + id_session
                resprest = requests.delete(url_delete_partner,
                                           headers=headers_data)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    resp = outputrest['resultado'] == 'OK'
                    if not resp:
                        error_message = outputrest['detalleError']
                url_close_session = url_remotecontrol_rest + \
                    '/sesiones/' + id_session
                resprest = requests.delete(url_close_session)
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    def unlink_partner_on_unlink_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unlink_telecontrol()
        self.unlink_partner_on_unlink('inelcom')

    # Implemented hook
    def synchronize_partner_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        error_message = ''
        observ = _('Source: Moval Regadío')
        observ_archived_preffix = _('Archived Data')
        if record_archived:
            observ = observ_archived_preffix + '. ' + observ
        pending_inv = 'NO'
        if data['with_credit_overdue']:
            pending_inv = 'SI'
        if url_remotecontrol_rest.endswith('/'):
            url_remotecontrol_rest = url_remotecontrol_rest[:-1]
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data,
                                     timeout=self.REQUEST_TIMEOUT)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                url_update_partner = url_remotecontrol_rest + \
                    '/regantes/' + str(data['partner_code']) + \
                    '?sesion=' + id_session
                resprest = requests.get(url_update_partner)
                exists_partner_in_remotecontrol = resprest.text != ''
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
                    'observaciones': observ,
                    'factPendientes': pending_inv,
                    }
                if exists_partner_in_remotecontrol:
                    resprest = requests.put(url_update_partner,
                                            data=json.dumps(payload_data),
                                            headers=headers_data)
                else:
                    del payload_data['nuevoNSocio']
                    resprest = requests.post(url_update_partner,
                                             data=json.dumps(payload_data),
                                             headers=headers_data,
                                             timeout=self.REQUEST_TIMEOUT)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    resp = outputrest['resultado'] == 'OK'
                    if not resp:
                        error_message = outputrest['detalleError']
                url_close_session = url_remotecontrol_rest + \
                    '/sesiones/' + id_session
                resprest = requests.delete(url_close_session)
        except Exception:
            resp = False
            error_message = _('Telecontrol Error')
        return resp, error_message

    def create_partner_on_synchronize_telecontrol(self):
        super(ResPartner, self).create_partner_on_synchronize_telecontrol()
        self.create_partner_on_syncrhonize('inelcom')

    # Implemented hook
    def synchronize_partners_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        partners_ok = []
        partners_not_ok = []
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data,
                                     timeout=self.REQUEST_TIMEOUT)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                for data in list_of_data:
                    observ = _('Source: Moval Regadío')
                    observ_archived_preffix = _('Archived Data')
                    current_partner = self.env['res.partner'].with_context(
                        active_test=False).search(
                            [('partner_code', '=', data['partner_code'])])
                    record_archived = not current_partner.active
                    if record_archived:
                        observ = observ_archived_preffix + '. ' + observ
                    pending_inv = 'NO'
                    if data['with_credit_overdue']:
                        pending_inv = 'SI'
                    url_update_partner = url_remotecontrol_rest + \
                        '/regantes/' + str(data['partner_code']) + \
                        '?sesion=' + id_session
                    resprest = requests.get(url_update_partner)
                    exists_partner_in_remotecontrol = resprest.text != ''
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
                        'observaciones': observ,
                        'factPendientes': pending_inv,
                        }
                    if exists_partner_in_remotecontrol:
                        resprest = requests.put(url_update_partner,
                                                data=json.dumps(payload_data),
                                                headers=headers_data)
                    else:
                        del payload_data['nuevoNSocio']
                        resprest = requests.post(url_update_partner,
                                                 data=json.dumps(payload_data),
                                                 headers=headers_data,
                                                 timeout=self.REQUEST_TIMEOUT)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        resp = outputrest['resultado'] == 'OK'
                        if resp:
                            partners_ok.append(data['partner_code'])
                        else:
                            partners_not_ok.append(data['partner_code'])
                url_close_session = url_remotecontrol_rest + \
                    '/sesiones/' + id_session
                resprest = requests.delete(url_close_session)
        except Exception:
            pass
        return partners_ok, partners_not_ok

    def create_partners_on_synchronize_telecontrol(self, active_partners):
        super(ResPartner, self).create_partners_on_synchronize_telecontrol(
            active_partners)
        self.create_partners_on_synchronize(active_partners, 'inelcom')

    def unlink_partner_on_unsynchronize_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unsynchronize_telecontrol()
        self.unlink_partner_on_unsyncrhonize('inelcom')

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
                resp = bankaccounts[0].acc_number.replace(' ', '')
                if len(resp) > 4:
                    resp = resp[4:]
        return resp
