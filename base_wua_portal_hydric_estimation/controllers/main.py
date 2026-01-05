# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http, _
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class WebsiteAccountHydricEstimation(website_account):

    def _prepare_portal_layout_values(self):
        values = super(WebsiteAccountHydricEstimation,
                       self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        values['partner'] = partner
        values['domain'] = ('partner_id', '=', partner.id)
        active_season_id = 0
        model_wua_agriculturalseason = \
            request.env['wua.agriculturalseason'].sudo()
        active_season = model_wua_agriculturalseason.search(
            [('active_agriculturalseason', '=', True)])
        if active_season:
            active_season_id = active_season[0].id
        initial_domain = [values['domain'],
                          ('agriculturalseason_id', '=', active_season_id)]
        values['cropunit_count'] = \
            request.env['wua.cropunit'].search_count(initial_domain)
        values['hydricneed_count'] = \
            request.env['wua.hydricneed'].search_count(initial_domain)
        values['active_season_id'] = active_season_id
        return values

    @http.route(['/my/cropunits', '/my/cropunits/page/<int:page>'],
                type='http', auth="user", website=True)
    def request_my_cropunits(self, page=1, sortby='name',
                             filterby='None', search=None,
                             search_in='cropunit', **kwargs):
        values = self._prepare_portal_layout_values()
        # Filters
        searchbar_filters = {
            'all_seasons': {'label': _('Any Season'), 'domain': []},
            'active_season': {'label': _('Active Season'),
                              'domain': [('agriculturalseason_id', '=',
                                          values['active_season_id'])]},
        }
        domain = searchbar_filters.get(
            filterby, searchbar_filters.get('active_season'))['domain']
        # TODO (provisional)
        domain.append(values['domain'])
        wua_cropunit_model = request.env['wua.cropunit']
        cropunits_page = wua_cropunit_model.search(domain)
        values.update({
            'cropunits_page': cropunits_page,
        })
        return request.render(
            'base_wua_portal_hydric_estimation.portal_my_cropunits',
            values,
        )
