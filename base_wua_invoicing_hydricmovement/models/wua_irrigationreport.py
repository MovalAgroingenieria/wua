# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    invoiced_irrigationreport_quota = fields.Boolean(
        string='Invoiced by quota',
        store=True,
        compute='_compute_invoiced_irrigationreport_quota')

    @api.depends('hydricmovement_ids',
                 'hydricmovement_ids.invoiced_hydricmovement')
    def _compute_invoiced_irrigationreport_quota(self):
        for record in self:
            result = False
            for hydricmov in record.hydricmovement_ids:
                if hydricmov.invoiced_hydricmovement:
                    result = True
                    break
            record.invoiced_irrigationreport_quota = result
