# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def get_partner_active_agriculturalseason_quotas(self):
        for record in self:
            quotas = self.env['wua.quota'].search([
                ('partner_id.id', '=', record.id),
                ('agriculturalseason_id.active_agriculturalseason',
                 '=', 'true'), ('accumulated_input', '>', 0)])
        return quotas
