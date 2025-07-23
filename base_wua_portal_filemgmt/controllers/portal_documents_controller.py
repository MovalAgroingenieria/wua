# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class PortalDocuments(http.Controller):

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        files = request.env['res.file.partnerlink']
        files_count = files.search_count(
            [('partner_id', '=', partner.id),
             ('file_id.available_on_portal', '=', True)])
        registries = request.env['res.letter']
        domain = [('state', '=', 'rec'),
                  '|',
                  ('recipient_partner_id', '=', partner.id),
                  ('sender_partner_id', '=', partner.id)]
        registries_count = registries.search_count(domain)
        registries_count = registries.search_count(domain)
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner,
            'files_count': files_count,
            'registries_count': registries_count,
        }
        return values

    @http.route(['/my/documents'],
                type='http', auth="user", website=True)
    def portal_my_documents(self):
        """ Redirects to the documents portal page """
        values = self._prepare_portal_layout_values()
        return request.render(
            "base_wua_portal_filemgmt.portal_my_documents",
            values)
