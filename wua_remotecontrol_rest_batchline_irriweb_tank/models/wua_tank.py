# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaTank(models.Model):
    _inherit = 'wua.tank'

    with_tankconsumptions = fields.Boolean(
        string="With Tankconsumptions",
        compute='_compute_with_tankconsumptions',
        store=True,
    )

    @api.depends('tankconsumption_ids')
    def _compute_with_tankconsumptions(self):
        for record in self:
            with_tankconsumptions = False
            if (record.tankconsumption_ids):
                with_tankconsumptions = len(record.tankconsumption_ids) > 0
            record.with_tankconsumptions = with_tankconsumptions
