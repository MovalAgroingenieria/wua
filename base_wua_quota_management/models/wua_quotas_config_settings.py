# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaQuotasConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.quotas.configuration'
    _description = 'Configuration of base_wua_quota_management module'

    sorted_quotas = fields.Boolean(
        string='Sort in superproducts',
        default=False,
        help='Apply superproduct sorting of quota periods to calculate '
             'the hydric consumptions')

    sorted_irrigationreport_quotas = fields.Boolean(
        string='Sort in superproducts for irrigation reports',
        default=False,
        help='Apply superproduct sorting of quota periods to calculate '
             'the irrigation reports consumptions')

    draft_cession_allow = fields.Boolean(
        string='Allow Draft State on Cessions',
        default=False)

    show_aggregated_quotas = fields.Boolean(
        string='Show aggregated quotas',
        default=False,
        help='If it is checked, it shows partner aggregated quotas.')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.quotas.configuration', 'sorted_quotas',
                           self.sorted_quotas)
        values.set_default('wua.quotas.configuration',
                           'sorted_irrigationreport_quotas',
                           self.sorted_irrigationreport_quotas)
        values.set_default('wua.quotas.configuration',
                           'draft_cession_allow',
                           self.draft_cession_allow)
        values.set_default('wua.quotas.configuration',
                           'show_aggregated_quotas',
                           self.show_aggregated_quotas)
        # If not allowed change of states, all cessions must be validated
        if (not self.draft_cession_allow):
            cessions_draft = self.env['wua.cession'].search(
                [('cession_state', '!=', '01_validated')])
            if (len(cessions_draft) > 0):
                raise exceptions.UserError(_(
                    'All cessions must be validated.'))
        if self.show_aggregated_quotas:
            active_menu = True
        else:
            active_menu = False
        query = """UPDATE ir_ui_menu SET active = %s
                   WHERE name = 'Partner aggregated quotas'""" % active_menu
        self.env.cr.execute(query)
        self.env.cr.commit()
