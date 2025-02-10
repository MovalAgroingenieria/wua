# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, api


class WuaAssembly(models.Model):
    _inherit = 'wua.assembly'

    @api.multi
    def _get_partners_domain(self):
        partners = super(WuaAssembly, self)._get_partners_domain()
        partners = partners.filtered(lambda partner: partner.is_primary)
        return partners
