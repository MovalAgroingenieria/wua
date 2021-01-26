# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaReportrequest(models.Model):
    _inherit = 'wua.reportrequest'

    mapped_irrigationreport_ids = fields.One2many(
        string='Irrigation reports',
        comodel_name='wua.irrigationreport',
        inverse_name='source_reportrequest_id')

    num_mapped_irrigationreport_ids = fields.Integer(
        string="Num. of associated reports",
        index=True,
        store=True,
        compute="_compute_num_mapped_irrigationreport_ids")

    @api.depends('mapped_irrigationreport_ids')
    def _compute_num_mapped_irrigationreport_ids(self):
        for record in self:
            if record.mapped_irrigationreport_ids:
                record.num_mapped_irrigationreport_ids = \
                    len(record.mapped_irrigationreport_ids)

#     @api.multi
#     def validate_reportrequest(self):
#         super(WuaReportrequest, self).validate_reportrequest()
#         self.ensure_one()
#         request = self
#         irrigation_report = False
#         irrigation_report = request.irrigationreport_id
#         if irrigation_report:
#             if irrigation_report.source_reportrequest_id.id == False:
#                 irrigation_report.source_reportrequest_id = \
#                     request.irrigationreport_id.id

    @api.multi
    def action_get_mapped_irrigationreport_ids(self):
        self.ensure_one()
        if self.mapped_irrigationreport_ids:
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
                'name': _('Irrigation reports'),
                'res_model': 'wua.irrigationreport',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.mapped_irrigationreport_ids.ids)]
                }
            return act_window
