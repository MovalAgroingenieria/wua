# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Static variables related to the GIS component.
    _gis_table = 'wua_gis_parcel'
    _geom_field = 'geom'
    _link_field = 'name'

    hydricneed_ids = fields.One2many(
        string='Associated hydric estimations',
        comodel_name='wua.hydricneed',
        inverse_name='parcel_id')

    mapped_to_polygon = fields.Boolean(
        string='Mapped to polygon',
        compute='_compute_mapped_to_polygon',
    )

    geom_ewkt = fields.Char(
        string='EWKT Geometry',
        compute='_compute_geom_ewkt',
    )

    @api.multi
    def _compute_mapped_to_polygon(self):
        geom_ok = self.geom_ok()
        for record in self:
            mapped_to_polygon = False
            if geom_ok:
                self.env.cr.execute("""
                    SELECT """ + self._link_field + """
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """='""" + record.name + """'
                    """)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get(self._link_field) is not None):
                    mapped_to_polygon = True
            record.mapped_to_polygon = mapped_to_polygon

    def _compute_geom_ewkt(self):
        geom_ok = self.geom_ok()
        for record in self:
            geom_ewkt = ''
            if geom_ok:
                self.env.cr.execute("""
                    SELECT postgis.st_asewkt(""" + self._geom_field + """)
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """
                    ='""" + record.name + """'""")
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('st_asewkt') is not None):
                    geom_ewkt = query_results[0].get('st_asewkt')
            record.geom_ewkt = geom_ewkt

    def geom_ok(self):
        resp = False
        try:
            self.env.cr.execute(
                'SELECT ' + self._link_field + ', ' + self._geom_field +
                ' FROM ' + self._gis_table + ' LIMIT 1')
            resp = True
        except Exception:
            pass
        return resp

    @api.multi
    def action_get_hydricneeds(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Irrigation Recommendations'),
            'res_model': 'wua.hydricneed',
            'view_type': 'form',
            'view_mode': 'tree,form,kanban,graph,pivot',
            'target': 'current',
            'domain': [('id', 'in', self.hydricneed_ids.ids)],
            'context': {'search_default_mapped_to_active_'
                        'agriculturalseason_yes': True,
                        'search_default_is_occurred_or_'
                        'current_controlperiod_yes': True},
        }
        return act_window

    @api.multi
    def get_ndvi_values_with_cropunits(self, parcel_ids, show_dialog=True):
        parcel_result = self.get_ndvi_values(parcel_ids, show_dialog=False)
        parcels = self.env['wua.parcel'].browse(parcel_ids)
        cropunit_ids = []
        for parcel in parcels:
            cropunits = self.env['wua.cropunit'].search([
                ('parcel_id', '=', parcel.id),
                ('agriculturalseason_id.active_agriculturalseason', '=', True)
            ])
            cropunit_ids.extend(cropunits.ids)
        cropunit_result = None
        if cropunit_ids:
            model_cropunit = self.env['wua.cropunit']
            cropunit_result = model_cropunit.get_ndvi_values_for_cropunits(
                cropunit_ids, show_dialog=False)
        if show_dialog:
            buttons = [{'type': 'ir.actions.act_window_close',
                        'name': _('Close')}]
            id_form_view = self.env.ref(
                'wua_remotesensing_sentinelhub_ndvi.'
                'wua_parcel_vegetationindex_ndvi_view_form').id
            id_tree_view = self.env.ref(
                'wua_remotesensing_sentinelhub_ndvi.'
                'wua_parcel_vegetationindex_ndvi_view_tree').id
            buttons.append({
                'type': 'ir.actions.act_window',
                'name': _('NDVI Parcels'),
                'res_model': 'wua.parcel.vegetationindex.ndvi',
                'view_mode': 'tree',
                'view_type': 'form',
                'views': [[id_tree_view, 'list'],
                          [id_form_view, 'form']],
                'context': {'search_default_active_agriculturalseason': True},
                'classes': 'btn-primary'})
            if cropunit_ids:
                id_form_view_cu = self.env.ref(
                    'base_wua_hydric_estimation.'
                    'wua_cropunit_vegetationindex_ndvi_view_form').id
                id_tree_view_cu = self.env.ref(
                    'base_wua_hydric_estimation.'
                    'wua_cropunit_vegetationindex_ndvi_view_tree').id
                buttons.append({
                    'type': 'ir.actions.act_window',
                    'name': _('NDVI Crop Units'),
                    'res_model': 'wua.cropunit.vegetationindex.ndvi',
                    'view_mode': 'tree',
                    'view_type': 'form',
                    'views': [[id_tree_view_cu, 'list'],
                              [id_form_view_cu, 'form']],
                    'context': {'search_default_active_agriculturalseason': True},
                    'classes': 'btn-info'})

            message_01 = _('OPERATION COMPLETED')
            message_02 = _('NDVI values captured for:')
            message_03 = _('- %s parcel(s)') % len(parcel_ids)
            message_04 = _('- %s crop unit(s)') % len(cropunit_ids) if cropunit_ids else _('- 0 crop units')
            message = '<center>' + message_01 + '</center><br>' + \
                message_02 + '<br>' + message_03 + '<br>' + message_04
            act_window = {
                'type': 'ir.actions.act_window.message',
                'title': _('Import NDVI values (Parcels + Crop Units)'),
                'message': message,
                'is_html_message': True,
                'close_button_title': False,
                'buttons': buttons
                }
            return act_window

