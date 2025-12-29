# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaCropfamily(models.Model):
    _name = 'wua.cropfamily'
    _description = 'Crop Family'
    _order = 'name'

    MAX_SIZE_NAME = 255

    def _default_kc_a(self):
        resp = 0
        default_kc_ndvi_a = self.env['ir.values'].get_default(
            'wua.configuration', 'default_kc_ndvi_a')
        if default_kc_ndvi_a:
            resp = default_kc_ndvi_a
        return resp

    def _default_kc_b(self):
        resp = 0
        default_kc_ndvi_b = self.env['ir.values'].get_default(
            'wua.configuration', 'default_kc_ndvi_b')
        if default_kc_ndvi_b:
            resp = default_kc_ndvi_b
        return resp

    def _default_kc_c(self):
        resp = 0
        default_kc_ndvi_c = self.env['ir.values'].get_default(
            'wua.configuration', 'default_kc_ndvi_c')
        if default_kc_ndvi_c:
            resp = default_kc_ndvi_c
        return resp

    name = fields.Char(
        string='Crop Family',
        size=MAX_SIZE_NAME,
        required=True,
        translate=True,
    )

    kc_a = fields.Float(
        string='Coefficient a in the quadratic function of Kc',
        default=_default_kc_a,
        digits=(32, 4),
        required=True,
    )

    kc_b = fields.Float(
        string='Coefficient b in the quadratic function of Kc',
        default=_default_kc_b,
        digits=(32, 4),
        required=True,
    )

    kc_c = fields.Float(
        string='Coefficient c in the quadratic function of Kc',
        default=_default_kc_c,
        digits=(32, 4),
        required=True,
    )

    kc_ndvi_low = fields.Float(
        string='Kc(0.0)',
        digits=(32, 2),
        compute='_compute_kc_ndvi_low',
    )

    kc_ndvi_medium = fields.Float(
        string='Kc(0.5)',
        digits=(32, 2),
        compute='_compute_kc_ndvi_medium',
    )

    kc_ndvi_hight = fields.Float(
        string='Kc(1.0)',
        digits=(32, 2),
        compute='_compute_kc_ndvi_hight',
    )

    kc_function = fields.Char(
        string='Kc(ndvi)',
        compute='_compute_kc_function'
    )

    hydricneed_ids = fields.One2many(
        string='Associated hydric estimations',
        comodel_name='wua.hydricneed',
        inverse_name='cropfamily_id')

    notes = fields.Text(
        string='Notes',
    )

    @api.multi
    def _compute_kc_ndvi_low(self):
        for record in self:
            record.kc_ndvi_low = record.calculate_kc(0.0)

    @api.multi
    def _compute_kc_ndvi_medium(self):
        for record in self:
            record.kc_ndvi_medium = record.calculate_kc(0.5)

    @api.multi
    def _compute_kc_ndvi_hight(self):
        for record in self:
            record.kc_ndvi_hight = record.calculate_kc(1.0)

    @api.multi
    def _compute_kc_function(self):
        for record in self:
            record.kc_function = \
                'Kc(ndvi) = ' + str(record.kc_a) + \
                ' · ndvi² + ' + str(record.kc_b) + \
                ' · ndvi + ' + str(record.kc_c)

    # Possible "hook" for other specializations.
    @api.multi
    def calculate_kc(self, ndvi=0.0):
        self.ensure_one()
        kc_lower_saturation = self.env['ir.values'].get_default(
            'wua.configuration', 'kc_lower_saturation')
        if not kc_lower_saturation:
            kc_lower_saturation = 0.0
        kc_upper_saturation = self.env['ir.values'].get_default(
            'wua.configuration', 'kc_upper_saturation')
        if not kc_upper_saturation:
            kc_upper_saturation = 0.0
        kc = (self.kc_a * pow(ndvi, 2)) + (self.kc_b * ndvi) + self.kc_c
        if kc_lower_saturation or kc_upper_saturation:
            if kc < kc_lower_saturation:
                kc = kc_lower_saturation
            if kc > kc_upper_saturation:
                kc = kc_upper_saturation
        return kc

    @api.multi
    def action_get_cultivations(self):
        self.ensure_one()
        current_cropfamily = self
        id_tree_view = self.env.ref(
            'base_wua_hydric_estimation.wua_cultivation_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_hydric_estimation.wua_cultivation_view_form').id
        search_view = self.env.ref(
            'base_wua_hydric_estimation.wua_cultivation_view_search')
        custom_context = \
            {'default_cropfamily_id': current_cropfamily.id}
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Cultivations'),
            'res_model': 'wua.cultivation',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('cropfamily_id', '=', current_cropfamily.id)],
            'context': custom_context,
            }
        return act_window

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
