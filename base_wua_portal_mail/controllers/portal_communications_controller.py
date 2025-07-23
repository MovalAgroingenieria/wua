# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class PortalCommunications(http.Controller):

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }
        return values

    @http.route(['/my/communications'],
                type='http', auth="user", website=True)
    def portal_my_communications(self):
        """ Redirects to the irrigation management portal page """
        values = self._prepare_portal_layout_values()
        return request.render(
            "base_wua_portal_mail.portal_my_communications",
            values)
