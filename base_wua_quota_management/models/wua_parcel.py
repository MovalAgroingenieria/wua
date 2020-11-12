# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    mapped_to_current_quotaperiod = fields.Boolean(
        string='In quotas',
        default=False,
        readonly=True)

    quotaperiodlineparcel_ids = fields.One2many(
        string='Quota Data',
        comodel_name='wua.quotaperiod.line.parcel',
        inverse_name='parcel_id')

    current_quotaperiod_id = fields.Many2one(
        string='Current Quota Period',
        comodel_name='wua.quotaperiod',
        compute='_compute_current_quotaperiod_id')

    @api.multi
    def _compute_current_quotaperiod_id(self):
        quotaperiod_model = self.env['wua.quotaperiod']
        for record in self:
            record.current_quotaperiod_id = \
                quotaperiod_model.get_current_generated_quotaperiod()

    @api.multi
    def action_get_quota_data(self):
        self.ensure_one()
        if self.quotaperiodlineparcel_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quotaperiod_line_parcel_quota_data_view_tree').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quotaperiod_line_parcel_quota_data_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Quota Data'),
                'res_model': 'wua.quotaperiod.line.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.quotaperiodlineparcel_ids.ids)]
                }
            return act_window

    @api.multi
    def action_assign_provision_not_confirm(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Initial provision for a parcel'),
            'res_model': 'wizard.provision.parcel',
            'src_model': 'wua.parcel',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    @api.multi
    def action_assign_provision_confirm(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Initial provision for the parcel'),
            'res_model': 'wizard.provision.parcel',
            'src_model': 'wua.parcel',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window
