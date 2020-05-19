# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaIrrigationreport(models.Model):
    _inherit = 'wua.irrigationreport'

    html_quota_balance = fields.Html(
        string='Balances',
        compute='_compute_html_quota_balance')

    @api.multi
    def _compute_html_quota_balance(self):
        for record in self:
            html_quota_balance = ''
            if record.partner_id:
                active_agriculturalseason = \
                    self.env['wua.agriculturalseason'].\
                    get_active_agriculturalseason()
                if (active_agriculturalseason and
                   active_agriculturalseason == record.agriculturalseason_id):
                    html_quota_balance = self._get_html_quota_balance(
                        record.partner_id)
            record.html_quota_balance = html_quota_balance

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.html_quota_balance = \
            self._get_html_quota_balance(self.partner_id)

    def _get_html_quota_balance(self, partner):
        resp = ''
        current_quotaperiod = self._get_current_quotaperiod()
        if current_quotaperiod:
            quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', current_quotaperiod.id),
                 ('partner_id', '=', partner.id)])
            if quotas:
                label_title = _('BALANCES')
                if len(quotas) == 1:
                    label_title = _('BALANCE')
                header = '<div class="text-center"><b><u>' + label_title + \
                         '</b></u></div>'
                body = ''
                for quota in quotas:
                    superproduct = '<b>' + quota.superproduct_id.name + '</b>'
                    balance = '%.2f' % quota.balance
                    if quota.balance < 0:
                        balance = '<p style="color:red">' + balance + '</p>'
                    body = body + '<br/>' + superproduct + ' : ' + balance
                resp = '<div class="panel-body text-left" ' + \
                       'style="background:#f4f6f6;border-radius:4px;' + \
                       'border-color:#696969;border-width:1px;' + \
                       'border-style:solid;padding-top:8px;' + \
                       'padding-bottom:11px;' + \
                       'margin-left:70px;margin-right:80px">' + \
                       header + body + '</div>'
        return resp

    # If there is active agricultural season, then: if this agricultural
    # season as single quota period, then the current quota period is that;
    # else the current quota period is the period of the current date.
    def _get_current_quotaperiod(self):
        resp = None
        active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if (active_agriculturalseason):
            quotaperiods = self.env['wua.quotaperiod'].search(
                [('agriculturalseason_id', '=', active_agriculturalseason.id),
                 ('state', '=', 'generated')],
                order='initial_date')
            if quotaperiods:
                if len(quotaperiods) == 1:
                    resp = quotaperiods[0]
                else:
                    current_time = datetime.datetime.now()
                    for quotaperiod in quotaperiods:
                        min_date = datetime.datetime.strptime(
                            quotaperiod.initial_date, '%Y-%m-%d')
                        max_date = datetime.datetime.strptime(
                            quotaperiod.end_date, '%Y-%m-%d') + \
                            datetime.timedelta(days=1)
                        if (current_time >= min_date and
                           current_time < max_date):
                            resp = quotaperiod
                            break
        return resp
