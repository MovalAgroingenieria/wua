# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _remotecontrol_partner_fields_hidroconta = [
        'partner_code', 'firstname', 'lastname', 'lastname2', 'vat',
        'street', 'street_num', 'zip', 'city', 'state_id', 'country_id',
        'phone', 'mobile', 'email'
    ]

    # Implemented hook
    def populate_data_for_send_new_partner_hidroconta(self, vals):
        resp = None
        installation_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        if vals and 'partner_code' in vals and installation_identifier:
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
            surname = ''
            if lastname:
                surname = lastname
                if lastname2:
                    surname = surname + ' ' + lastname2
                firstname = firstname + ' ' + surname
            vat = self.get_val(vals, 'vat')
            if not vat:
                vat = '-'
            if len(vat) > 2:
                vat = vat[2:]
            street = self.get_val(vals, 'street')
            street_num = self.get_val(vals, 'street_num')
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
            address = ''
            if street:
                address = street
                if street_num:
                    address = address + ', ' + street_num
                address = address + '. '
            if city:
                address = address + zipcode + ' ' + city
                if state and country:
                    address = address + ' (' + state + ', ' + country + ')'
            phone = self.get_val(vals, 'phone')
            mobile = self.get_val(vals, 'mobile')
            phones = self.get_phones(phone, mobile)
            email = self.get_val(vals, 'email')
            resp = {
                'name': firstname,
                'surname': surname,
                'nif': vat,
                'enabled': 'true',
                'address': address,
                'phoneNumber': phones,
                'email': email,
                'parcel': '',
                'censusId': partner_code,
                'installationId': installation_identifier,
                }
        return resp

    # Implemented hook
    def send_new_partner_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'GET', url_remotecontrol_rest + '/owners?' +
                'param=censusId&value=' + str(data['censusId']),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
            if resprest.status_code == 200 and resprest.text != '[]':
                error_message = _('The partner already exists')
            else:
                resprest = requests.request(
                    'POST', url_remotecontrol_rest + '/owners',
                    headers={
                        'Content-Type': 'application/json',
                        'Cookie': 'JSESSIONID=' + jsessionid
                        },
                    data=json.dumps(data))
                if resprest.status_code == 201:
                    resp = True
                else:
                    error_message = resprest.text
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    def send_partner_on_creation_telecontrol(self, new_partner, vals):
        super(ResPartner, self).send_partner_on_creation_telecontrol(
            new_partner, vals
        )
        self.send_partner_on_creation('hidroconta', new_partner, vals)

    # Implemented hook
    def populate_data_for_update_partner_hidroconta(self, partner):
        resp = None
        installation_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        if partner and installation_identifier:
            partner_code = partner.partner_code
            if (partner.is_company):
                firstname = self.refine_value(partner.name)
                lastname = ''
                lastname2 = ''
            else:
                firstname = self.refine_value(partner.firstname)
                lastname = self.refine_value(partner.lastname)
                lastname2 = self.refine_value(partner.lastname2)
            surname = ''
            if lastname:
                surname = lastname
                if lastname2:
                    surname = surname + ' ' + lastname2
                firstname = surname + ', ' + firstname
            vat = self.refine_value(partner.vat)
            if not vat:
                vat = '-'
            if len(vat) > 2:
                vat = vat[2:]
            street = self.refine_value(partner.street)
            street_num = self.refine_value(partner.street_num)
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
            address = ''
            if street:
                address = street
                if street_num:
                    address = address + ', ' + street_num
                address = address + '. '
            if city:
                address = address + zipcode + ' ' + city
                if state and country:
                    address = address + ' (' + state + ', ' + country + ')'
            phone = self.refine_value(partner.phone)
            mobile = self.refine_value(partner.mobile)
            phones = self.get_phones(phone, mobile)
            email = self.refine_value(partner.email)
            resp = {
                'name': firstname,
                'surname': surname,
                'nif': vat,
                'enabled': 'true',
                'address': address,
                'phoneNumber': phones,
                'email': email,
                'parcel': '',
                'censusId': partner_code,
                'installationId': installation_identifier,
                }
        return resp

    # Implemented hook
    def update_partner_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'GET', url_remotecontrol_rest + '/owners?' +
                'param=censusId&value=' + str(data['censusId']),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
            if resprest.status_code == 200 and resprest.text == '[]':
                error_message = _('The partner does not exists')
            else:
                ownerId = 0
                owners = json.loads(resprest.text)
                if len(owners) > 1:
                    error_message = _('There are several owners with the ' +
                                      'same code')
                else:
                    ownerId = owners[0]['ownerId']
                    data['ownerId'] = ownerId
                    resprest = requests.request(
                        'PUT', url_remotecontrol_rest + '/owners',
                        headers={
                            'Content-Type': 'application/json',
                            'Cookie': 'JSESSIONID=' + jsessionid
                            },
                        data=json.dumps(data))
                    if resprest.status_code == 200:
                        resp = True
                    else:
                        error_message = resprest.text
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    def send_partner_on_write_telecontrol(self, vals):
        super(ResPartner, self).send_partner_on_write_telecontrol(vals)
        self.send_partner_on_write('hidroconta', vals)

    # Implemented hook
    def populate_data_for_delete_partner_hidroconta(self, partner):
        resp = None
        if partner:
            partner_code = partner.partner_code
            resp = {
                'partner_code': partner_code,
                }
        return resp

    # Implemented hook
    def delete_partner_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'GET', url_remotecontrol_rest + '/owners?' +
                'param=censusId&value=' + str(data['partner_code']),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
            if resprest.status_code == 200 and resprest.text == '[]':
                error_message = _('The partner does not exists')
            else:
                ownerId = 0
                owners = json.loads(resprest.text)
                if len(owners) > 1:
                    error_message = _('There are several owners with the ' +
                                      'same code')
                else:
                    ownerId = owners[0]['ownerId']
                    resp = True
                    resprest = requests.request(
                        'DELETE', url_remotecontrol_rest + '/owners/' +
                        str(ownerId),
                        headers={
                            'Content-Type': 'application/json',
                            'Cookie': 'JSESSIONID=' + jsessionid
                            },
                        data={})
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    def unlink_partner_on_unlink_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unlink_telecontrol()
        self.unlink_partner_on_unlink('hidroconta')

    # Implemented hook
    def synchronize_partner_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
        url_remotecontrol_rest_password,
            data, record_archived=False):
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'GET', url_remotecontrol_rest + '/owners?' +
                'param=censusId&value=' + str(data['censusId']),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
            if resprest.status_code == 200:
                exists_partner_in_remotecontrol = resprest.text != '[]'
                if not exists_partner_in_remotecontrol:
                    resprest = requests.request(
                        'POST', url_remotecontrol_rest + '/owners',
                        headers={
                            'Content-Type': 'application/json',
                            'Cookie': 'JSESSIONID=' + jsessionid
                            },
                        data=json.dumps(data))
                    if resprest.status_code == 201:
                        resp = True
                    else:
                        error_message = resprest.text
                else:
                    ownerId = 0
                    owners = json.loads(resprest.text)
                    if len(owners) > 1:
                        error_message = _('There are several owners with the' +
                                          ' same code')
                    else:
                        ownerId = owners[0]['ownerId']
                        data['ownerId'] = ownerId
                        resprest = requests.request(
                            'PUT', url_remotecontrol_rest + '/owners',
                            headers={
                                'Content-Type': 'application/json',
                                'Cookie': 'JSESSIONID=' + jsessionid
                                },
                            data=json.dumps(data))
                        if resprest.status_code == 200:
                            resp = True
                        else:
                            error_message = resprest.text
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    def create_partner_on_synchronize_telecontrol(self):
        super(ResPartner, self).create_partner_on_synchronize_telecontrol()
        self.create_partner_on_syncrhonize('hidroconta')

    # Implemented hook
    def synchronize_partners_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        partners_ok = []
        partners_not_ok = []
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            for data in list_of_data:
                resprest = requests.request(
                    'GET', url_remotecontrol_rest + '/owners?' +
                    'param=censusId&value=' + str(data['censusId']),
                    headers={
                        'Content-Type': 'application/json',
                        'Cookie': 'JSESSIONID=' + jsessionid
                        },
                    data={})
                if resprest.status_code == 200:
                    exists_partner_in_remotecontrol = resprest.text != '[]'
                    if not exists_partner_in_remotecontrol:
                        resprest = requests.request(
                            'POST', url_remotecontrol_rest + '/owners',
                            headers={
                                'Content-Type': 'application/json',
                                'Cookie': 'JSESSIONID=' + jsessionid
                                },
                            data=json.dumps(data))
                        if resprest.status_code == 201:
                            partners_ok.append(data['censusId'])
                        else:
                            partners_not_ok.append(data['censusId'])
                    else:
                        ownerId = 0
                        owners = json.loads(resprest.text)
                        if len(owners) > 1:
                            partners_not_ok.append(data['censusId'])
                        else:
                            ownerId = owners[0]['ownerId']
                            data['ownerId'] = ownerId
                            resprest = requests.request(
                                'PUT', url_remotecontrol_rest + '/owners',
                                headers={
                                    'Content-Type': 'application/json',
                                    'Cookie': 'JSESSIONID=' + jsessionid
                                    },
                                data=json.dumps(data))
                            if resprest.status_code == 200:
                                partners_ok.append(data['censusId'])
                            else:
                                partners_not_ok.append(data['censusId'])
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return partners_ok, partners_not_ok

    def create_partners_on_synchronize_telecontrol(self, active_partners):
        super(ResPartner, self).create_partners_on_synchronize_telecontrol(
            active_partners)
        self.create_partners_on_synchronize(active_partners, 'hidroconta')

    def unlink_partner_on_unsynchronize_telecontrol(self):
        super(ResPartner, self).unlink_partner_on_unsynchronize_telecontrol()
        self.unlink_partner_on_unsyncrhonize('hidroconta')

    def get_phones(self, phone, mobile):
        resp = ''
        if (phone or mobile):
            if phone:
                resp = phone
                if mobile:
                    resp = resp + ", " + mobile
            else:
                resp = mobile
        return resp

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
