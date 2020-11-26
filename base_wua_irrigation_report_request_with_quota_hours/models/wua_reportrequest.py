# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class WuaReportrequest(models.Model):
    _inherit = 'wua.reportrequest'

    # Overwrite original method
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
                    balance = self.env['wua.parcel'].transform_float_to_locale(
                        quota.balance, 2)
                    balance = balance + _(' m³')
                    balance_hours = \
                        self.env['wua.quota'].transform_to_quota_hours_format(
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
