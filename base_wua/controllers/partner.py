# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import base64
from odoo import http, _
from odoo.http import request


class PartnerShpController(http.Controller):

    @http.route('/pubshp', type='http', auth='public', methods=['GET'],
                website=True)
    def get_parcel_shp(self, **kwargs):
        resp = '{"parcel_shp":""}'
        partner = kwargs.get('partner', False)
        in_base64 = int(kwargs.get('base64', 0)) == 1
        if partner:
            model_res_partner = request.env['res.partner'].sudo()
            model_wua_configuration = request.env['ir.values'].sudo()
            name_partner_model = model_res_partner.__class__.__name__
            ip_remote_addr = request.httprequest.environ['REMOTE_ADDR']
            allowed_ip_remote_address = model_wua_configuration.get_default(
                'wua.configuration', 'ip_remote_address_for_shp')
            if (not allowed_ip_remote_address or
               allowed_ip_remote_address == ip_remote_addr):
                partner = model_res_partner.search(
                    [('partner_code', '=', partner)])
                parcels_of_partner = partner.partnerlink_ids.mapped(
                    lambda x: x.parcel_id)
                parcel_shp = parcels_of_partner.generate_parcel_shp()
                if parcel_shp:
                    _logger = logging.getLogger(name_partner_model)
                    _logger.info('Parcel SHP requested from http-get, '
                                 'NO credentials. Partner: ' +
                                 str(partner.partner_code) +
                                 '. Client IP Address: ' + ip_remote_addr)
                    if in_base64 == 1:
                        resp = '{"parcel_shp":"' + \
                            parcel_shp + '"}'
                    else:
                        parcels_label = _('Parcels')
                        content = base64.b64decode(parcel_shp)
                        zip_httpheaders = [
                            ('Content-Type', 'application/zip'),
                            ('Content-Length', len(content)),
                            ('Content-Disposition',
                             'attachment; filename="' + parcels_label +
                             '.zip"')]
                        resp = request.make_response(
                            content, headers=zip_httpheaders)
        return resp

    @http.route('/prishp', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def get_certificate_with_auth(self, **kwargs):
        resp = _('No SHP: The user must be a portal user, or '
                 'it is not possible to obtain SHP outside of the '
                 'main program.')
        current_user = request.env.user
        if current_user and current_user.partner_id:
            partner = current_user.partner_id
            model_res_partner = request.env['res.partner'].sudo()
            name_partner_model = model_res_partner.__class__.__name__
            ip_remote_addr = request.httprequest.environ['REMOTE_ADDR']
            parcels_of_partner = partner.partnerlink_ids.mapped(
                lambda x: x.parcel_id)
            parcel_shp = parcels_of_partner.generate_parcel_shp()
            if parcel_shp:
                _logger = logging.getLogger(name_partner_model)
                _logger.info('Parcel SHP requested from http-get. '
                             'Partner: ' + str(partner.partner_code) +
                             '. Client IP Address: ' + ip_remote_addr)
                parcels_label = _('Parcels')
                content = base64.b64decode(parcel_shp)
                zip_httpheaders = [
                    ('Content-Type', 'application/zip'),
                    ('Content-Length', len(content)),
                    ('Content-Disposition',
                        'attachment; filename="' + parcels_label +
                        '.zip"')]
                resp = request.make_response(
                    content, headers=zip_httpheaders)
        request.session.logout()
        return resp
