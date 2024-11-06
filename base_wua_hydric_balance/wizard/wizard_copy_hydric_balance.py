# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WizardCopyHydricBalance(models.TransientModel):
    _name = 'wizard.copy.hydric.balance'
    _description = 'Wizard to Copy Hydric Balance'

    new_initial_date = fields.Date(
        string='New Initial Date',
        required=True,
    )
    new_end_date = fields.Date(
        string='New End Date',
        required=True,
    )

    def action_copy_hydric_balance(self):
        self.ensure_one()
        hydric_balance_id = self.env.context.get('active_id')
        hydric_balance = \
            self.env['wua.hydric.balance'].browse(hydric_balance_id)
        hydric_balance._do_copy(
            new_initial_date=self.new_initial_date,
            new_end_date=self.new_end_date)
