# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import models, fields, api, exceptions, _


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

    selected_for_current_quotaperiod = fields.Boolean(
        string='Parcel present in the current quota period',
        default=False,
        compute='_compute_selected_for_current_quotaperiod')

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

    @api.multi
    def _compute_selected_for_current_quotaperiod(self):
        for record in self:
            selected_for_current_quotaperiod = False
            self.partnerlink_ids.__class__._fired_onchange_partner = False
            self.partnerlink_ids.__class__._fired_onchange_watercosts = False
            current_date = datetime.today().strftime('%Y-%m-%d')
            if record.id > 0:
                self.env.cr.execute("""
                    select count(*)
                    from wua_quotaperiod_line_parcel qplp
                    inner join wua_quotaperiod_line qpl
                    on qplp.quotaperiodline_id = qpl.id
                    inner join wua_quotaperiod qp on
                    qpl.quotaperiod_id = qp.id
                    where qplp.selected = true and qp.state='generated' and
                    qp.initial_date <= %s and qp.end_date >= %s and
                    qplp.parcel_id = %s""", (current_date,
                                             current_date, record.id))
                query_results = self.env.cr.dictfetchall()
                if (query_results and query_results[0].get('count') is not None
                   and query_results[0].get('count') > 0):
                    selected_for_current_quotaperiod = True
            record.selected_for_current_quotaperiod = \
                selected_for_current_quotaperiod


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    _fired_onchange_partner = False
    _fired_onchange_watercosts = False

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if (self.parcel_id.selected_for_current_quotaperiod and
           self.partner_id and
           self.water_costs_percentage and
           (not self.__class__._fired_onchange_partner)):
            self.__class__._fired_onchange_partner = True
            warning_title = _('IMPORTANT WARNING:')
            warning_text = _('A change has been detected in the partners '
                             'that take charge of the water costs. Consider '
                             'making any necessary adjustments to the '
                             'distribution of the affected quotas, or click '
                             'DISCARD to undo the change.')
            raise exceptions.UserError(warning_title + '\n\n' + warning_text)

    @api.onchange('water_costs_percentage')
    def _onchange_watercosts(self):
        if (self.parcel_id.selected_for_current_quotaperiod and
           self.partner_id and
           (not self.__class__._fired_onchange_watercosts)):
            self.__class__._fired_onchange_watercosts = True
            warning_title = _('IMPORTANT WARNING:')
            warning_text = _('A change in the percentage of water costs of '
                             'the parcel has been detected. Consider making '
                             'the necessary adjustments to the distribution '
                             'of the affected quotas, or click DISCARD to '
                             'undo the change.')
            raise exceptions.UserError(warning_title + '\n\n' + warning_text)
