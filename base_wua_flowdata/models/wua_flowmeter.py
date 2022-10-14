# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_associated = fields.Selection(
        [],
        string='Type of telecontrol associated')

    flowdata_ids = fields.One2many(
        string='Flow measurements',
        comodel_name='wua.flowdata',
        inverse_name='flowmeter_id')

    number_of_flowdata_ids = fields.Integer(
        string="Num. flowdata",
        compute="_compute_number_of_flowdata_ids")

    @api.multi
    def _compute_number_of_flowdata_ids(self):
        for record in self:
            number_of_flowdata_ids = len(record.flowdata_ids)
            record.number_of_flowdata_ids = number_of_flowdata_ids

    @api.multi
    def action_see_flowdata(self):
        self.ensure_one()
        condition = [('flowmeter_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_flowdata.wua_flowdata_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_flowdata.wua_flowdata_view_tree').id
        search_view = self.env.ref(
            'base_wua_flowdata.wua_flowdata_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Flow data'),
            'res_model': 'wua.flowdata',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
