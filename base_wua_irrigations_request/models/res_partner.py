# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irrigationsrequest_ids = fields.One2many(
        string="Irrigations Requests",
        comodel_name="wua.irrigationsrequest",
        inverse_name="partner_id")

    number_of_irrigationsrequest = fields.Integer(
        string="N. of Irrigations Requests",
        compute="_compute_number_of_irrigationsrequest")

    @api.depends('irrigationsrequest_ids')
    def _compute_number_of_irrigationsrequest(self):
        for record in self:
            number_of_irrigationsrequest = 0
            if record.irrigationsrequest_ids:
                number_of_irrigationsrequest = len(
                    record.irrigationsrequest_ids)
            record.number_of_irrigationsrequest = number_of_irrigationsrequest

    @api.multi
    def action_see_irrigationsrequests(self):
        self.ensure_one()
        if self.irrigationsrequest_ids:
            id_tree_view = self.env.ref(
                'base_wua_irrigations_request.'
                'wua_irrigationsrequest_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_irrigations_request.'
                'wua_irrigationsrequest_view_form').id
            search_view = self.env.ref(
                'base_wua_irrigations_request.'
                'wua_irrigationsrequest_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Irrigations Requests'),
                'res_model': 'wua.irrigationsrequest',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.irrigationsrequest_ids.ids)]
                }
            return act_window
