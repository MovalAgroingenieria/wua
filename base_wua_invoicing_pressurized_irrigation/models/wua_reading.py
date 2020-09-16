# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _description = 'Entity (pressure reading)'

    invoiced_reading = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced_reading')

    @api.depends('presconsumption_id',
                 'presconsumption_id.invoiced_consumption')
    def _compute_invoiced_reading(self):
        for record in self:
            invoiced_reading = False
            if record.presconsumption_id:
                invoiced_reading = \
                    record.presconsumption_id.invoiced_consumption
            record.invoiced_reading = invoiced_reading
