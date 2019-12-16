# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    irrigationreport_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.irrigationreport",
        inverse_name="agriculturalseason_id")

    number_of_irrigationreports = fields.Integer(
        string="N. of Irrig. Reports",
        index=True,
        store=True,
        compute="_compute_number_of_irrigationreports")

    num_irrigationreports_stat = fields.Integer(
        string="N. Reports",
        compute="_compute_num_irrigationreports_stat")

    total_volume = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 4),
        store=True,
        compute="_compute_total_volume")

    @api.depends('irrigationreport_ids')
    def _compute_number_of_irrigationreports(self):
        for record in self:
            number_of_irrigationreports = 0
            if record.irrigationreport_ids:
                number_of_irrigationreports = len(record.irrigationreport_ids)
            record.number_of_irrigationreports = number_of_irrigationreports

    @api.multi
    def _compute_num_irrigationreports_stat(self):
        for record in self:
            record.num_irrigationreports_stat = \
                record.number_of_irrigationreports

    @api.depends('irrigationreport_ids', 'irrigationreport_ids.volume_real')
    def _compute_total_volume(self):
        for record in self:
            total_volume = 0.0
            for irrigationreport in record.irrigationreport_ids:
                total_volume += irrigationreport.volume_real
            record.total_volume = total_volume

    @api.multi
    def action_see_irrigationreports(self):
        self.ensure_one()
        if self.irrigationreport_ids:
            id_tree_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_form').id
            search_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Irrigation Reports'),
                'res_model': 'wua.irrigationreport',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.irrigationreport_ids.ids)]
                }
            return act_window
