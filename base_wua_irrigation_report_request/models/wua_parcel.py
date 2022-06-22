# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    reportrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.reportrequest",
        inverse_name="parcel_id")

    number_of_reportrequests = fields.Integer(
        string="N. of Report requests",
        index=True,
        store=True,
        compute="_compute_number_of_reportrequests")

    @api.depends('reportrequest_ids')
    def _compute_number_of_reportrequests(self):
        for record in self:
            number_of_reportrequests = 0
            if record.reportrequest_ids:
                number_of_reportrequests = len(record.reportrequest_ids)
            record.number_of_reportrequests = number_of_reportrequests

    @api.multi
    def action_see_reportrequests(self):
        self.ensure_one()
        if self.reportrequest_ids:
            id_tree_view = self.env.ref(
                'base_wua_irrigation_report_request.'
                'wua_reportrequest_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_irrigation_report_request.'
                'wua_reportrequest_view_form').id
            search_view = self.env.ref(
                'base_wua_irrigation_report_request.'
                'wua_reportrequest_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Report Requests'),
                'res_model': 'wua.reportrequest',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.reportrequest_ids.ids)]
                }
            return act_window
