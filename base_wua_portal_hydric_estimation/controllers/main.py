# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http, _
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class WebsiteAccountHydricEstimation(website_account):

    # Number of records per page.
    _items_per_page = 10

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
                             filterby='active_season', search=None,
                             search_in='cropunit'):
        values = self._prepare_portal_layout_values()
        # Filters.
        searchbar_filters = {
            'all_seasons': {'label': _('Any Season'), 'domain': []},
            'active_season': {'label': _('Active Season'),
                              'domain': [('agriculturalseason_id', '=',
                                          values['active_season_id'])]},
        }
        domain = searchbar_filters.get(
            filterby, searchbar_filters.get(filterby))['domain']
        # Search.
        if search_in and search:
            cropunit_ids = []
            sql_statement = \
                ('SELECT id FROM wua_cropunit WHERE '
                 'name iLIKE \'%s\'' % ('%' + search + '%', ))
            if search_in == 'cultivation':
                frontend_lang = request.env.lang
                sql_statement = \
                    ('SELECT cu.id FROM wua_cropunit cu '
                     'INNER JOIN wua_cultivation c '
                     'ON cu.cultivation_id = c.id '
                     'INNER JOIN ir_translation t '
                     'ON t.res_id = c.id AND t.type = \'model\' AND '
                     't.name = \'wua.cultivation,name\' AND t.lang = \'%s\' '
                     'WHERE cu.partner_id = %s AND '
                     't.value iLIKE \'%s\' ' %
                     (frontend_lang, values['partner'].id, '%' + search + '%'))
            request.env.cr.execute(sql_statement)
            sql_resp = request.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    cropunit_ids.append(item[0])
            search_condition = ('id', 'in', cropunit_ids)
            domain.append(search_condition)
        domain.append(values['domain'])
        # Sorting.
        searchbar_sortings = {
            'name': 'name asc',
            'area_gis_ha': 'area_gis_ha asc',
            'sum_total_gin': 'sum_total_gin asc',
        }
        order = searchbar_sortings.get(sortby, 'name asc')
        # Pager.
        wua_cropunit_model = request.env['wua.cropunit']
        cropunit_count = wua_cropunit_model.search_count(domain)
        url_args = {}
        if filterby:
            url_args['filterby'] = filterby
        if search_in:
            url_args['search_in'] = search_in
        if search:
            url_args['search'] = search
        if sortby:
            url_args['sortby'] = sortby
        pager = request.website.pager(
            url="/my/cropunits",
            total=cropunit_count,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        # Final filter.
        cropunits_page = wua_cropunit_model.search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset'])
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'cropunits_page': cropunits_page,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'pager': pager,
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            'base_wua_portal_hydric_estimation.portal_my_cropunits',
            values,
        )

    @http.route(['/my/hydricneeds', '/my/hydricneeds/page/<int:page>'],
                type='http', auth="user", website=True)
    def request_my_hydricneeds(self, page=1, sortby='name_desc',
                               filterby='active_season', search=None,
                               search_in='cropunit'):
        values = self._prepare_portal_layout_values()
        # Filters.
        searchbar_filters = {
            'all_seasons': {'label': _('Any Season'), 'domain': []},
            'active_season': {'label': _('Active Season'),
                              'domain': [('agriculturalseason_id', '=',
                                          values['active_season_id'])]},
        }
        domain = searchbar_filters.get(
            filterby, searchbar_filters.get(filterby))['domain']
        # Search.
        if search_in and search:
            hydricneed_ids = []
            sql_statement = \
                ('SELECT hn.id FROM wua_hydricneed hn '
                 'INNER JOIN wua_cropunit cu '
                 'ON hn.cropunit_id = cu.id '
                 'WHERE cu.name iLIKE \'%s\'' % ('%' + search + '%', ))
            if search_in == 'cultivation':
                frontend_lang = request.env.lang
                sql_statement = \
                    ('SELECT hn.id FROM wua_hydricneed hn '
                     'INNER JOIN wua_cropunit cu ON hn.cropunit_id = cu.id '
                     'INNER JOIN wua_cultivation c '
                     'ON cu.cultivation_id = c.id '
                     'INNER JOIN ir_translation t '
                     'ON t.res_id = c.id AND t.type = \'model\' AND '
                     't.name = \'wua.cultivation,name\' AND t.lang = \'%s\' '
                     'WHERE cu.partner_id = %s AND '
                     't.value iLIKE \'%s\' ' %
                     (frontend_lang, values['partner'].id, '%' + search + '%'))
            request.env.cr.execute(sql_statement)
            sql_resp = request.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    hydricneed_ids.append(item[0])
            search_condition = ('id', 'in', hydricneed_ids)
            domain.append(search_condition)
        domain.append(values['domain'])
        # Sorting.
        searchbar_sortings = {
            'name_desc': 'initial_date desc, name asc',
            'name_asc': 'initial_date asc, name asc',
            'area_gis_ha': 'area_gis_ha asc',
            'total_gin': 'total_gin asc',
        }
        order = searchbar_sortings.get(sortby, 'initial_date desc, name asc')
        # Pager.
        wua_hydricneed_model = request.env['wua.hydricneed']
        hydricneed_count = wua_hydricneed_model.search_count(domain)
        url_args = {}
        if filterby:
            url_args['filterby'] = filterby
        if search_in:
            url_args['search_in'] = search_in
        if search:
            url_args['search'] = search
        if sortby:
            url_args['sortby'] = sortby
        pager = request.website.pager(
            url="/my/hydricneeds",
            total=hydricneed_count,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        # Final filter.
        hydricneeds_page = wua_hydricneed_model.search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset'])
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal',
        )
        values.update({
            'hydricneeds_page': hydricneeds_page,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'pager': pager,
            'liquidation_on_portal': liquidation_on_portal,
        })
        return request.render(
            'base_wua_portal_hydric_estimation.portal_my_hydricneeds',
            values,
        )

    @http.route('/new_cropunit', type='http', auth="user", website=True,
                methods=['POST'])
    def request_new_observation(self):
        values = self._prepare_portal_layout_values()
        # TODO (provisional)
        return request.render(
            'base_wua_portal_hydric_estimation.portal_new_cropunit',
            values,
        )

    @http.route('/confirm', type='http', auth="user", website=True,
                methods=['POST'])
    def request_confirm_cropunit(self, **kwargs):
        initial_date = kwargs.get('initial_date', '')
        end_date = kwargs.get('end_date', '')
        # TODO (provisional)
        print initial_date
        print end_date
        return request.redirect('/my/cropunits')
