
# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.http import request
from odoo.addons.base_wua_portal.controllers.portal_parcels_controller import PortalParcels


class PortalParcels(PortalParcels):

    @http.route(['/my/parcels/<int:parcel>'], type='http',
                auth="user", website=True)
    def parcels_followup(self, parcel=None, ids=None, **kw):
        response = super(PortalParcels, self).parcels_followup(
            parcel=parcel, ids=ids, **kw)
        if (isinstance(
                response, http.Response) and hasattr(response, 'qcontext')):
            model = request.env['wua.sigpac']
            selection = model._fields['uso_sigpac'].selection
            response.qcontext['uso_sigpac_dict'] = dict(selection)
        return response
