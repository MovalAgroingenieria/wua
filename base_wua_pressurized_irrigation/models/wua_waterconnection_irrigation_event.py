# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from lxml import etree


class WuaWaterconnectionIrrigationEvent(models.Model):
    _name = 'wua.waterconnection.irrigation.event'
    _description = 'Entity (waterconnection irrigation event)'
    _order = 'irrigation_end_date desc'

    # TODO Max Size Name:
    MAX_SIZE_NAME = 52

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='cascade',
    )

    irrigation_start_date = fields.Datetime(
        string='Irrigation Start Date',
        required=True,
    )

    irrigation_end_date = fields.Datetime(
        string='Irrigation End Date',
        required=True,
    )

    irrigation_duration = fields.Float(
        string='Irigation Duration',
        digits=(32, 2),
        store=True,
        compute='_compute_irrigation_duration',
    )

    irrigation_volume = fields.Float(
        string='Irigation Volume (m³)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    irrigation_flow = fields.Float(
        string='Irigation Flow (m³/h)',
        digits=(32, 4),
        store=True,
        compute='_compute_irrigation_flow',
    )

    irrigation_area = fields.Float(
        string='Irrigation Area (U)',
        digits=(32, 4),
        store=True,
        compute='_compute_irrigation_area',
    )

    irrigation_area_static = fields.Float(
        string='Irrigation Area (Static)',
        digits=(32, 4),
        default=-1.0,
    )

    irrigation_flow_per_surface = fields.Float(
        string='Irigation Flow Per Surface (m³/U/h)',
        digits=(32, 4),
        store=True,
        compute='_compute_irrigation_flow_per_surface',
    )

    name = fields.Char(
        string='Irrigation Event',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Irrigation Event.'),
        ]

    @api.depends('waterconnection_id', 'irrigation_start_date',
                 'irrigation_end_date')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.irrigation_start_date and \
                    record.irrigation_end_date:
                value = record.waterconnection_id.name + u'-' + \
                    str(record.irrigation_start_date) + u'-' + str(
                        record.irrigation_end_date)
            record.name = value

    @api.depends('irrigation_start_date', 'irrigation_end_date')
    def _compute_irrigation_duration(self):
        for record in self:
            irrigation_duration = 0.0
            if (record.irrigation_start_date and record.irrigation_end_date):
                irrigation_duration = (
                    fields.Datetime.from_string(record.irrigation_end_date) -
                    fields.Datetime.from_string(record.irrigation_start_date)
                ).total_seconds() / 3600
            record.irrigation_duration = irrigation_duration

    @api.depends('irrigation_volume', 'irrigation_duration')
    def _compute_irrigation_flow(self):
        for record in self:
            irrigation_flow = 0.0
            if (record.irrigation_volume and record.irrigation_duration):
                irrigation_flow = record.irrigation_volume / \
                    record.irrigation_duration
            record.irrigation_flow = irrigation_flow

    @api.depends('waterconnection_id', 'irrigation_area_static')
    def _compute_irrigation_area(self):
        for record in self:
            irrigation_area = 0.0
            # If irrigation area static is setted, use it instead of the
            # Calculus
            if (record.irrigation_area_static >= 0):
                irrigation_area = record.irrigation_area_static
            elif (record.waterconnection_id and
                    record.waterconnection_id.irrigationpoint_ids):
                irrigation_area = sum(
                    record.waterconnection_id.irrigationpoint_ids.mapped(
                        lambda x: x.parcel_area_official))
            record.irrigation_area = irrigation_area

    @api.depends('irrigation_area', 'irrigation_flow')
    def _compute_irrigation_flow_per_surface(self):
        for record in self:
            irrigation_flow_per_surface = 0
            if (record.irrigation_area and record.irrigation_flow):
                irrigation_flow_per_surface = record.irrigation_flow / \
                    record.irrigation_area
            record.irrigation_flow_per_surface = \
                irrigation_flow_per_surface

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaWaterconnectionIrrigationEvent, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            # Info of area uom
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            else:
                area_measurement_name = _('ha')
            for node in doc.xpath(
                    "//field[@name='irrigation_area']"):
                original_label = \
                    self.env['wua.parcel'].sudo().get_value_from_translation(
                        'base_wua_pressurized_irrigation',
                        self.__class__.irrigation_area.string)
                label = original_label.replace('U', area_measurement_name)
                node.set('string', label)
            for node in doc.xpath(
                    "//field[@name='irrigation_flow_per_surface']"):
                original_label = \
                    self.env['wua.parcel'].sudo().get_value_from_translation(
                        'base_wua_pressurized_irrigation',
                        self.__class__.irrigation_flow_per_surface.string.
                        decode('utf_8'))
                label = original_label.replace('U', area_measurement_name)
                node.set('string', label)
            res['arch'] = etree.tostring(doc)
        return res
