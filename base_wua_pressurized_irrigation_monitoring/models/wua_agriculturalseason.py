# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
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
        string='Estimated Consumption (m3)',
        digits=(32, 4),
        compute='_compute_estimated_consumption',
        store=True
    )

    real_consumption = fields.Float(
        string='Real Consumption (m3)',
        digits=(32, 4),
        compute='_compute_real_consumption',
        store=True
    )

    deviation = fields.Float(
        string='Deviation (m3)',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True
    )

    deviation_percentage = fields.Char(
        string='Deviation Percentage',
        compute='_compute_deviation_percentage',
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
            deviation = record.real_consumption - record.estimated_consumption
            record.deviation = deviation

    @api.multi
    def _compute_deviation_percentage(self):
        for record in self:
            if record.estimated_consumption == 0 and \
                    record.real_consumption == 0:
                record.deviation_percentage = '0%'
            else:
                deviation_percentage = 100
                is_negative = False
                deviation = record.deviation
                if deviation < 0:
                    deviation = abs(deviation)
                    is_negative = True
                if deviation > 0 and record.estimated_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.estimated_consumption
                if is_negative:
                    deviation_percentage = deviation_percentage * -1
                record.deviation_percentage = \
                    '{:.2f}'.format(deviation_percentage) + '%'

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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(WuaAgriculturalseason, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            unit = _('(m³/agriculturalseason)')
            for node in doc.xpath("//field[@name='estimated_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.estimated_consumption.string)
                node.set('string', original_label + ' ' + unit)
            for node in doc.xpath("//field[@name='real_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.real_consumption.string)
                node.set('string', original_label + ' ' + unit)
            for node in doc.xpath("//field[@name='deviation']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.deviation.string)
                node.set('string', original_label + ' ' + unit)
            res['arch'] = etree.tostring(doc)
        return res
