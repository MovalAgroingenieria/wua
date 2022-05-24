# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from base64 import encodestring
from odoo import http, _
from odoo.http import request


class CertificateController(http.Controller):

    @http.route('/pubcert', type='http', auth='public', methods=['GET'],
                website=True)
    def get_certificate(self, **kwargs):
        resp = '{"certificate":""}'
        partner = kwargs.get('partner', False)
        type_of_certificate = int(kwargs.get('type', 1))
        portal_user = int(kwargs.get('portal', 1)) == 1
        in_base64 = int(kwargs.get('base64', 0)) == 1
        pdf_in_server = kwargs.get('pdf', '')
        if partner:
            if pdf_in_server:
                if pdf_in_server[0] != '/':
                    pdf_in_server = '/tmp/' + pdf_in_server
                if pdf_in_server[-3:].lower() != 'pdf':
                    pdf_in_server = pdf_in_server + '.pdf'
            model_wua_certificate = request.env['wua.certificate'].sudo()
            model_wua_configuration = request.env['ir.values'].sudo()
            name_certificate_model = model_wua_certificate.__class__.__name__
            ip_remote_addr = request.httprequest.environ['REMOTE_ADDR']
            allowed_ip_remote_address = model_wua_configuration.get_default(
                'wua.configuration', 'ip_remote_address')
            if (not allowed_ip_remote_address or
               allowed_ip_remote_address == ip_remote_addr):
                certificate = model_wua_certificate.get_validated_certificate(
                    partner, type_of_certificate, portal_user, pdf_in_server)
                if certificate:
                    _logger = logging.getLogger(name_certificate_model)
                    _logger.info('Certificate create from http-get, '
                                 'NO credentials. Partner: ' + partner +
                                 '. Client IP Address: ' + ip_remote_addr)
                    if in_base64 == 1:
                        resp = '{"certificate":"' + \
                            encodestring(certificate) + '"}'
                    else:
                        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                                          ('Content-Length', len(certificate))]
                        resp = request.make_response(certificate,
                                                     headers=pdfhttpheaders)
        return resp

    @http.route('/pricert', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def get_certificate_with_auth(self, **kwargs):
        resp = _('No certificate: The user must be a portal user, or '
                 'it is not possible to obtain certificates outside of the '
                 'main program.')
        current_user = request.env.user
        if current_user and current_user.partner_id:
            partner = current_user.partner_id.partner_code
            if partner:
                partner = str(partner)
                model_wua_certificate = request.env['wua.certificate'].sudo()
                model_wua_configuration = request.env['ir.values'].sudo()
                name_certificate_model = \
                    model_wua_certificate.__class__.__name__
                ip_remote_addr = request.httprequest.environ['REMOTE_ADDR']
                allowed_request_for_portal_user = \
                    model_wua_configuration.get_default(
                        'wua.configuration', 'allowed_request_for_portal_user')
                if allowed_request_for_portal_user:
                    type_of_certificate = 1
                    portaluser_certificatetype_id = \
                        model_wua_configuration.get_default(
                            'wua.configuration',
                            'portaluser_certificatetype_id')
                    if portaluser_certificatetype_id:
                        certificatetype = \
                            request.env['wua.certificate.type'].browse(
                                portaluser_certificatetype_id)
                        if certificatetype:
                            type_of_certificate = \
                                certificatetype.certificatetype_code
                    certificate = \
                        model_wua_certificate.get_validated_certificate(
                            partner, type_of_certificate, True, '')
                    if certificate:
                        _logger = logging.getLogger(name_certificate_model)
                        _logger.info('Certificate create from http-get, '
                                     'normal authentication. Partner: ' +
                                     partner +
                                     '. Client IP Address: ' + ip_remote_addr)
                        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                                          ('Content-Length', len(certificate))]
                        resp = request.make_response(certificate,
                                                     headers=pdfhttpheaders)
        request.session.logout()
        return resp
