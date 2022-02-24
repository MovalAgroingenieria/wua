# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreditCommunication(models.TransientModel):
    _inherit = "credit.control.communication"

    def _get_ordered_lines(self, credit_lines_ids):
        ordered_lines = self.env['credit.control.line'].search(
            [('id', 'in', credit_lines_ids)], order='date_due asc')
        return ordered_lines
