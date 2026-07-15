# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class HydricBalanceManager(models.Model):
    _name = "hydric.balance.manager"
    _description = "Hydric Balance Manager"
    _inherit = ["moval.external.app.screen.abstract"]

    APP_SLUG = "balances-hidricos"

    @api.model
    def _get_form_view_xmlid(self):
        return "wua_hydric_balance_manager.hydric_balance_manager_home"
