# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class WuaAssembly(models.Model):
    _inherit = 'wua.assembly'

    def _get_partners_domain(self):
        partner_domain = super(WuaAssembly, self)._get_partners_domain()
        partner_domain.append(['is_primary', '=', True])
        return partner_domain
