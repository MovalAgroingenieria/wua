# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.irrigation.configuration'
    _description = 'Configuration of base_wua_pressurized_irrigation module ' \
        'and base_wua_gravity_irrigation module)'

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS (SELECT * FROM information_schema.tables
            WHERE table_name='wua_irrigation_configuration')
            """)
        if not self.env.cr.fetchone()[0]:
            self.env.cr.execute("""
                DELETE from ir_values
                WHERE model = 'wua.irrigation.configuration'
                """)

    default_watermeter_type = fields.Selection([
        ('undefined', 'Undefined'),
        ('multistream', 'Multi-stream'),
        ('woltmann', 'Woltmann'),
        ('electromagnetic', 'Electromagnetic'),
        ('ultrasonic', 'Ultrasonic')],
        string='Water Meter Type',
        default='undefined',
        help='When create a new water meter, default type')

    default_wateringtime_perunitarea = fields.Integer(
        string='Watering Min./Area U.',
        default=0,
        help='Default watering time per area unit '
             '(if the chosen irrigation ditch does not have this value)')

    default_volume_perunitime = fields.Integer(
        string='Litres/Sec.',
        default=0,
        help='Default volume, as litres per second '
             '(if the chosen irrigation ditch does not have this value)')

    default_only_cultivable_subparcel = fields.Boolean(
        string='Only cultivable',
        default=True,
        help='For watering, only cultivable subparcels will be considerated')

    default_calculation_model = fields.Selection([
        (1, 'Constant Irrigation Allocation'),
        (2, 'Only on Request'),
        (3, 'Mixed Mode')],
        'Calculation Model',
        help='Calculation Model for watering')

    default_distribute_extra_volume = fields.Boolean(
        string='Distribute extra vol.',
        default=True,
        help='After watering calculation, distribute extra volume')

    watering_req_duration_threshold_active = fields.Boolean(
        string='With thresold',
        default=False,
        help='If true, there will be a maximum duration '
             'for the requested subparcel waterings')

    watering_req_duration_threshold_factor = fields.Float(
        string='Custom factor',
        digits=(32, 5),
        default=1,
        required=True,
        help='The maximum duration of a requested subparcel watering '
             'will be the product of the "Watering Min./Area U." '
             'and this custom factor')

    watering_req_duration_threshold_only_portal_users = fields.Boolean(
        string='Only for portal users',
        default=True)

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'default_watermeter_type',
                           self.default_watermeter_type)
        values.set_default('wua.irrigation.configuration',
                           'default_wateringtime_perunitarea',
                           self.default_wateringtime_perunitarea)
        values.set_default('wua.irrigation.configuration',
                           'default_volume_perunitime',
                           self.default_volume_perunitime)
        values.set_default('wua.irrigation.configuration',
                           'default_only_cultivable_subparcel',
                           self.default_only_cultivable_subparcel)
        values.set_default('wua.irrigation.configuration',
                           'default_calculation_model',
                           self.default_calculation_model)
        values.set_default('wua.irrigation.configuration',
                           'default_distribute_extra_volume',
                           self.default_distribute_extra_volume)
        values.set_default('wua.irrigation.configuration',
                           'watering_req_duration_threshold_active',
                           self.watering_req_duration_threshold_active)
        values.set_default('wua.irrigation.configuration',
                           'watering_req_duration_threshold_factor',
                           self.watering_req_duration_threshold_factor)
        values.set_default('wua.irrigation.configuration',
                           'watering_req_duration_threshold_only_portal_users',
                           self.
                           watering_req_duration_threshold_only_portal_users)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationConfiguration, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            irrigation_model_type = int(self.env['ir.values'].get_default(
                'wua.infrastructure.configuration', 'irrigation_model_type'))
            if irrigation_model_type != 2:
                doc = etree.XML(res['arch'])
                if irrigation_model_type == 0:
                    for node in doc.xpath("//group[@name='grav_irrig']"):
                        node.set('modifiers', '{"invisible": true}')
                    for node in doc.xpath("//group[@name='watering_req']"):
                        node.set('modifiers', '{"invisible": true}')
                if irrigation_model_type == 1:
                    for node in doc.xpath("//group[@name='pres_irrig']"):
                        node.set('modifiers', '{"invisible": true}')
                res['arch'] = etree.tostring(doc)
        return res
