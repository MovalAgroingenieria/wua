# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    validated = fields.Boolean(
        string='Validated',
        store=True,
        compute='_compute_validated')

    @api.depends('reading_id', 'reading_id.validated')
    def _compute_validated(self):
        for record in self:
            validated = False
            if record.reading_id.validated:
                validated = True
            record.validated = validated
