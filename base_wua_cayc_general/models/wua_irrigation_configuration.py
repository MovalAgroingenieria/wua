# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    independent_lock_modification_hours = fields.Integer(
        string="Lock Modification Hours for Independent partners",
        required=True,
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        old_independent_lock_modification_hours = values.get_default(
            'wua.irrigation.configuration',
            'independent_lock_modification_hours')
        values.set_default('wua.irrigation.configuration',
                           'independent_lock_modification_hours',
                           self.independent_lock_modification_hours)
        if (old_independent_lock_modification_hours !=
                self.independent_lock_modification_hours):
            self.env['wua.presresconsumption'].search(
                [('state', '=', '01_draft')])._compute_modification_deadline()
