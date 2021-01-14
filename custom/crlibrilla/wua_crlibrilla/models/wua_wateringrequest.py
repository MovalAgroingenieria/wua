# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'

    @api.model
    def create(self, vals):
        has_notes = ""
        if 'gravconsumption_ids' in vals and 'notes' in vals:
            has_gravconsumptions = vals.get('gravconsumption_ids')
            has_notes = vals.get('notes')
        if has_notes and has_gravconsumptions:
            gravconsumption_ids = vals['gravconsumption_ids']
            grav_vals = _('<b>Notes from watering request:</b>') + \
                vals['notes']
            for gravconsumption in gravconsumption_ids:
                gravconsumption[2]['notes'] = grav_vals
        return super(WuaWateringrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        has_notes = ""
        if 'notes' in vals:
            has_notes = vals.get('notes')
            if has_notes:
                grav_vals = _('<b>Notes from watering request:</b>') + \
                    vals['notes']
            if 'gravconsumption_ids' in vals:
                has_gravconsumptions = vals.get('gravconsumption_ids')
                if has_gravconsumptions:
                    gravconsumption_ids = vals['gravconsumption_ids']
                    for gravconsumption in gravconsumption_ids:
                        if gravconsumption[2]:
                            gravconsumption[2]['notes'] = grav_vals
            else:
                gravconsumption_ids = \
                    self.env['wua.gravconsumption'].search(
                        [('wateringrequest_id', '=', self.id)])
                for gravconsumption in gravconsumption_ids:
                    gravconsumption.notes = grav_vals
        return super(WuaWateringrequest, self).write(vals)

    # This method detects if the base_wua_gravity_irrigation_with_quota_hours
    # module is installed and performs the same modifications.
    def _get_html_quota_balance(self, partner):
        resp = ''
        current_quotaperiod = self._get_current_quotaperiod()
        if current_quotaperiod:
            quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', current_quotaperiod.id),
                 ('partner_id', '=', partner.id),
                 ('accumulated_input', '>', 0)])
            if quotas:
                label_title = _('BALANCES')
                if len(quotas) == 1:
                    label_title = _('BALANCE')
                header = '<div class="text-center"><b><u>' + label_title + \
                         '</b></u></div>'
                body = ''
                hours_module = self.sudo().env['ir.module.module'].search([
                    ('name', '=',
                     'base_wua_gravity_irrigation_with_quota_hours'),
                    ('state', '=', 'installed')])
                for quota in quotas:
                    superproduct = '<b>' + quota.superproduct_id.name + '</b>'
                    balance = self.env['wua.parcel'].transform_float_to_locale(
                        quota.balance, 2)
                    balance = balance + _(' m³')
                    if hours_module:
                        balance_hours = \
                            self.env[
                                'wua.quota'].transform_to_quota_hours_format(
                                quota.balance)
                        balance_hours = balance_hours + _(' hours')
                        balance = balance + ' | ' + balance_hours
                    if quota.balance < 0:
                        balance = '<span style="color:red">' + balance + \
                            '</span>'
                    body = body + '<br/>' + superproduct + ' : ' + balance
                resp = '<div class="panel-body text-left" ' + \
                       'style="background:#f4f6f6;border-radius:4px;' + \
                       'border-color:#696969;border-width:1px;' + \
                       'border-style:solid;padding-top:8px;' + \
                       'padding-bottom:11px;' + \
                       'margin-left:70px;margin-right:80px">' + \
                       header + body + '</div>'
        return resp
