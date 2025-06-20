# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    maximum_nominal_flow = fields.Float(
        string='Maximum nominal flow (l/s)',
        digits=(32, 4),
        compute='_compute_maximum_nominal_flow',
    )

    from_san_salvador_pumping = fields.Boolean(
        string='From San Salvador Pumping',
        default=False,
    )

    from_san_salvador_gravity = fields.Boolean(
        string='From San Salvador Gravity',
        default=False,
    )

    from_san_salvador_esplus = fields.Boolean(
        string='From San Salvador Esplús',
        default=False,
    )

    @api.multi
    def _compute_maximum_nominal_flow(self):
        for record in self:
            maximum_nominal_flow = 0.0
            if (record.watermeter_id and
                    record.watermeter_id.maximum_nominal_flow):
                maximum_nominal_flow = record.watermeter_id.\
                    maximum_nominal_flow
            record.maximum_nominal_flow = maximum_nominal_flow

