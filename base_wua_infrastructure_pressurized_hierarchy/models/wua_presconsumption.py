# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        comodel_name='wua.waterpipe',
        store=True,
        compute='_compute_waterpipe_id',
        ondelete='restrict')

    @api.depends('watermeter_id', 'watermeter_id.irrigationshed_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_value = None
            if record.watermeter_id and record.watermeter_id.irrigationshed_id:
                waterpipe_value = \
                    record.watermeter_id.irrigationshed_id.waterpipe_id
            record.waterpipe_id = waterpipe_value
