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
