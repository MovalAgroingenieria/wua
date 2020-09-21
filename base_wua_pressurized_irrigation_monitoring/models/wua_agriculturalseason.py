# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    controlperiod_ids = fields.One2many(
        string='Control Periods',
        comodel_name='wua.controlperiod',
        inverse_name='agriculturalseason_id'
    )

    number_of_controlperiods = fields.Integer(
        string='Number of control periods',
        store=True,
        compute='_compute_number_of_controlperiods'
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4),
        compute='_compute_estimated_consumption',
        store=True
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4),
        compute='_compute_real_consumption',
        store=True
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True
    )

    @api.depends('controlperiod_ids')
    def _compute_number_of_controlperiods(self):
        for record in self:
            record.number_of_controlperiods = \
                len(record.controlperiod_ids)

    @api.depends('controlperiod_ids',
                 'controlperiod_ids.estimated_consumption')
    def _compute_estimated_consumption(self):
        for record in self:
            estimated_consumption = 0
            if (record.number_of_controlperiods > 0):
                for controlperiod in record.controlperiod_ids:
                    estimated_consumption += \
                        controlperiod.estimated_consumption
            record.estimated_consumption = estimated_consumption

    @api.depends('controlperiod_ids', 'controlperiod_ids.real_consumption')
    def _compute_real_consumption(self):
        for record in self:
            real_consumption = 0
            if (record.number_of_controlperiods > 0):
                for controlperiod in record.controlperiod_ids:
                    real_consumption += controlperiod.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.multi
    def write(self, vals):
        resp = super(WuaAgriculturalseason, self).write(vals)
        if len(self) == 1:
            if 'active_agriculturalseason' in vals:
                subparcels = self.env['wua.parcel.subparcel'].search([])
                if subparcels:
                    subparcels._compute_estimated_consumption()
                    subparcels._compute_real_consumption()
        return resp

    def get_wua_agriculturalseason_comparative_presconsumption_action(self):
        current_agriculturalseason_id = self.env.context.get('active_id')
        condition = [('agriculturalseason_id', '=',
                     current_agriculturalseason_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Subparcels'),
            'res_model': 'wua.comparative.subparcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_controlperiod': True},
            }
        return act_window

    def get_wua_agriculturalseason_control_presconsumption_action(self):
        current_agriculturalseason_id = self.env.context.get('active_id')
        condition = [('agriculturalseason_id', '=',
                     current_agriculturalseason_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Control Consumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': self.env.context,
            }
        return act_window
