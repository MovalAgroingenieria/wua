# -*- coding: utf-8 -*-).
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaNegativeFlowreading(models.Model):
    _inherit = 'wua.negative.flowreading'

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        store=True,
        compute='_compute_connection_data',
        ondelete='restrict')

    @api.depends('flowmeter_id')
    def _compute_connection_data(self):
        for record in self:
            intake_id_value = None
            waterpipe_id_value = None
            if record.flowmeter_id:
                intake_id_value = record.flowmeter_id.intake_id
                waterpipe_id_value = record.flowmeter_id.waterpipe_id
            record.intake_id = intake_id_value
            record.waterpipe_id = waterpipe_id_value
