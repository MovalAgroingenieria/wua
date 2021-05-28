# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    wausms_ids = fields.One2many(
        string="SMS's sent",
        comodel_name='wausms.tracking',
        inverse_name='parcel_id')

    num_sms = fields.Integer(
        string="Number of SMS",
        compute="_compute_num_sms")

    @api.multi
    def _compute_num_sms(self):
        for record in self:
            record.num_sms = len(record.wausms_ids)

    @api.multi
    def action_see_wausms_parcel(self):
        tree_view = self.env.ref('wausms_client_sms.wausms_tracking_view_tree')
        form_view = self.env.ref('wausms_client_sms.wausms_tracking_view_form')
        return {
            'name': _('SMS'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'wausms.tracking',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('id', 'in', self.wausms_ids.ids)],
        }
