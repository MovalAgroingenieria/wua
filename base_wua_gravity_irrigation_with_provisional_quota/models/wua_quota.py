# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaQuota(models.Model):
    _description = 'Quota'
    _inherit = 'wua.quota'

    def _get_available_quota(self, quota):
        return quota.provisional_balance
