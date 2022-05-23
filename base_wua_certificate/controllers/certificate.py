# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from base64 import encodestring
from odoo import http
from odoo.http import request


class CertificateController(http.Controller):

    @http.route('/pubcert', type='http', auth='public', methods=['GET'],
                website=True)
    def get_certificate(self, **kwargs):
        partner = kwargs.get('partner', False)
        type_of_certificate = kwargs.get('type', 1)
        portal_user = kwargs.get('portal', 0)
        in_base64 = kwargs.get('base64', 0)
        pdf_in_server = kwargs.get('pdf', '')
        resp = '{"certificate":""}'
        if partner:
            if pdf_in_server:
                pdf_in_server = '/tmp/' + pdf_in_server
                if pdf_in_server[-3:].lower() != 'pdf':
                    pdf_in_server = pdf_in_server + '.pdf'
            model_wua_certificate = request.env['wua.certificate'].sudo()
            model_name = model_wua_certificate.__class__.__name__
            ip_remote_addr = request.httprequest.environ['REMOTE_ADDR']
            resp = model_wua_certificate.get_validated_certificate(
                partner, type_of_certificate, portal_user, pdf_in_server)
            _logger = logging.getLogger(model_name)
            _logger.info('Certificate create from http-get, '
                         'NO credentials. Client IP '
                         'Address: ' + ip_remote_addr)
            print in_base64
            if in_base64 == '1':
                print "aquíiiiii"
                resp = '{"certificate":"' + encodestring(resp) + '"}'
            else:
                pdfhttpheaders = [('Content-Type', 'application/pdf'),
                                  ('Content-Length', len(resp))]
                resp = request.make_response(resp, headers=pdfhttpheaders)
        return resp

    @http.route('/pricert', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def get_certificate_with_auth(self, **kwargs):
        partner = kwargs.get('partner', False)
        type_of_certificate = kwargs.get('type', 1)
        portal_user = kwargs.get('portal', 0)
        pdf_in_server = kwargs.get('pdf', '')
        if partner:
            if pdf_in_server:
                pdf_in_server = '/tmp/' + pdf_in_server
                if pdf_in_server[-3:].lower() != 'pdf':
                    pdf_in_server = pdf_in_server + '.pdf'
            partner_code = 0
            if partner.isdigit():
                partner_code = partner
            else:
                vat = partner
                if len(vat) > 2:
                    if (vat[0:1].isdigit() or vat[1:2].isdigit()):
                        vat = 'ES' + vat
                else:
                    return False
            partner_id = 0
            if partner_code:
                partners = request.env['res.partner'].sudo().search(
                    [('partner_code', '=', partner_code)])
            else:
                partners = request.env['res.partner'].sudo().search(
                    [('vat', '=', vat), ('is_wua_partner', '=', True)])
            if partners:
                partner_id = partners[0].id
            if partner_id:
                print request.env.context.get('uid')
                request.env['wua.certificate'].sudo(
                    ).get_validated_certificate(partner, type_of_certificate,
                                                portal_user, pdf_in_server)
                last_certificate = request.env['wua.certificate'].search(
                    [('partner_id', '=', partner_id)],
                    limit=1, order='name desc')
                if last_certificate:
                    certificate_id = last_certificate[0].id
                    pdf = request.env['report'].sudo().get_pdf(
                        [certificate_id],
                        'base_wua_certificate.report_wua_certificate',
                        data=None)
                    pdfhttpheaders = [('Content-Type', 'application/pdf'),
                                      ('Content-Length', len(pdf))]
                    return request.make_response(pdf, headers=pdfhttpheaders)
        return False
