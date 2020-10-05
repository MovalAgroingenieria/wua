# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    invoiced_reading_quota = fields.Boolean(
        string='Invoiced by quota',
        store=True,
        compute='_compute_invoiced_quota_reading')

    @api.depends('presconsumption_id',
                 'presconsumption_id.invoiced_consumption_quota')
    def _compute_invoiced_quota_reading(self):
        for record in self:
            invoiced_quota_reading = False
            if record.presconsumption_id:
                invoiced_quota_reading = \
                    record.presconsumption_id.invoiced_consumption_quota
            record.invoiced_reading = invoiced_quota_reading
