# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    reportrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.reportrequest",
        inverse_name="partner_id")

    number_of_reportrequest = fields.Integer(
        string="N. of Reports Requests",
        compute="_compute_number_of_reportrequest")

    @api.depends('reportrequest_ids')
    def _compute_number_of_reportrequest(self):
        for record in self:
            number_of_reportrequest = 0
            if record.reportrequest_ids:
                number_of_reportrequest = len(record.reportrequest_ids)
            record.number_of_reportrequest = number_of_reportrequest

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
