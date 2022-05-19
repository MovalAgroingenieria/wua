# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import http
from odoo.http import request


class CertificateController(http.Controller):

    @http.route('/pubcert', type='http', auth='public', methods=['GET'],
                website=True)
    def get_certificate(self, **kwargs):
        partner = kwargs.get('partner', False)
        type_of_certificate = kwargs.get('type', 1)
        portal_user = kwargs.get('portal', 0)
        pdf_in_server = kwargs.get('pdf', '')
        resp = ''
        if partner:
            if pdf_in_server:
                pdf_in_server = '/tmp/' + pdf_in_server
                if pdf_in_server[-3:].lower() != 'pdf':
                    pdf_in_server = pdf_in_server + '.pdf'
            resp = request.env['wua.certificate'].sudo(
                ).get_validated_certificate(partner, type_of_certificate,
                                            portal_user, pdf_in_server)
            # Provisional
            # partner = request.env['res.partner'].sudo().search(
            #     [('partner_code', '=', partner)])
            # return ('{"identification":"' + partner +
            #         ',"cert_type":' + str(type_of_certificate) +
            #         ',"is_portal_user":' + str(portal_user) +
            #         ',"pdf_file":' + pdf_in_server + '}')
        return '{"certificate":"' + resp + '"}'
