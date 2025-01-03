# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaQuotaperiodLine(models.Model):
    _inherit = 'wua.quotaperiod.line'

    def _get_where_clause(self):
        where_clause = super(WuaQuotaperiodLine, self)._get_where_clause()
        where_clause += ' AND is_primary '
        return where_clause
