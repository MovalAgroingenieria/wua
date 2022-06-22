# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    irrigationreport_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.irrigationreport",
        inverse_name="parcel_id")

    number_of_irrigationreports = fields.Integer(
        string="N. of Irrig. Reports",
        index=True,
        store=True,
        compute="_compute_number_of_irrigationreports")

    @api.depends('irrigationreport_ids')
    def _compute_number_of_irrigationreports(self):
        for record in self:
            number_of_irrigationreports = 0
            if record.irrigationreport_ids:
                number_of_irrigationreports = len(record.irrigationreport_ids)
            record.number_of_irrigationreports = number_of_irrigationreports

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
