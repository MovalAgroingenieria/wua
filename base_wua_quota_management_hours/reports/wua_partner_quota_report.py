# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def recalcule_quota_total_hours(self, total_m3):
        total_hours = \
            self.env['wua.quota'].transform_to_quota_hours_format(total_m3)
        return total_hours
