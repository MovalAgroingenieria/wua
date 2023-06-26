# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Error on 2022-12-29 Modification where hydricmovement has lost reference
    # account_invoice_line table, restore the presconsumption ones
    env = api.Environment(cr, SUPERUSER_ID, {})
    ails = env['account.invoice.line'].search(
        [('presconsumption_id', '!=', None),
         ('hydricmovement_id', '=', None),
         ('create_date', '>=', '2022-12-29')])
    for ail in ails:
        if (ail.presconsumption_id.invoiced_consumption_quota):
            ail.hydricmovement_id = ail.presconsumption_id.\
                hydricmovement_ids[0]
