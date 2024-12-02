# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    preswateringperiod_ids = fields.One2many(
        string='Watering Periods',
        comodel_name='wua.preswateringperiod',
        inverse_name='agriculturalseason_id',
    )

    number_of_preswateringperiods = fields.Integer(
        string='Number of preswateringperiods',
        compute='_compute_number_of_preswateringperiods',
        compute_sudo=True,
    )

    @api.multi
    def _compute_number_of_preswateringperiods(self):
        for record in self:
            number_of_preswateringperiods = 0
            if (record.number_of_preswateringperiods):
                number_of_preswateringperiods = \
                    len(record.preswateringperiod_ids)
            record.number_of_preswateringperiods = \
                number_of_preswateringperiods

    def action_see_preswateringperiods(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preswatering Periods'),
            'res_model': 'wua.preswateringperiod',
            'view_mode': 'tree,form',
            'domain': [('agriculturalseason_id', '=', self.id)],
            'target': 'current',
        }
