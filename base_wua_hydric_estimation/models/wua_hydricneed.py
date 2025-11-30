# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime

from odoo import models, fields, api, exceptions, _


class WuaHydricneed(models.Model):
    _name = 'wua.hydricneed'
    _description = 'Hydric needs of the crop units'
    _order = 'name desc'

    cropunit_id = fields.Many2one(
        string='Crop Unit',
        comodel_name='wua.cropunit',
        index=True,
        required=True,
        ondelete='cascade',
    )

    monitoringperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.monitoringperiod',
        index=True,
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Code',
        store=True,
        index=True,
        compute='_compute_name', )

    mean_ndvi = fields.Float(
        string='Mean NDVI',
        digits=(32, 4),
        default=0,
        required=True,
        index=True)

    accumulated_et0 = fields.Float(
        string='Accumulated ET0',
        digits=(32, 4),
        default=0,
        required=True,
        index=True)

    accumulated_pe = fields.Float(
        string='Accumulated Pe',
        digits=(32, 4),
        default=0,
        required=True,
        index=True)

    kc = fields.Float(
        string='Kc',
        digits=(32, 4),
        compute='_compute_kc',
    )

    accumulated_etc = fields.Float(
        string='Accumulated ETc',
        digits=(32, 4),
        compute='_compute_accumulated_etc',
    )

    nin = fields.Float(
        string='Net Irrigation Needs',
        digits=(32, 2),
        default=0,
        required=True,
        index=True)

    gin = fields.Float(
        string='Gross Irrigation Needs',
        digits=(32, 2),
        default=0,
        store=True,
        index=True,
        compute='_compute_gin',
    )

    total_gin = fields.Float(
        string='Total gross irrigation needs',
        digits=(32, 2),
        default=0,
        store=True,
        index=True,
        compute='_compute_total_gin',
    )

    initial_date = fields.Date(
        string='Control period dates',
        store=True,
        index=True,
        compute='_compute_initial_date',
    )

    end_date = fields.Date(
        string='End date',
        store=True,
        index=True,
        compute='_compute_end_date',
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        compute='_compute_agriculturalseason_id',
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        store=True,
        index=True,
        compute='_compute_parcel_id',
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        store=True,
        index=True,
        compute='_compute_cultivation_id',
    )

    order_number = fields.Integer(
        string='Order Number',
        store=True,
        index=True,
        compute='_compute_order_number',
    )

    is_current_controlperiod = fields.Boolean(
        string='Current Control Period (y/n)',
        related='monitoringperiod_id.is_current_controlperiod',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'Existing hydric need.'),
        ('mean_ndvi_ok',
         'CHECK (mean_ndvi >= -1 and mean_ndvi <= 1)',
         'The NDVI value must be between -1 and 1.'),
        ('accumulated_et0',
         'CHECK (accumulated_et0 >= 0)',
         'The accumulated ET0 value cannot be negative.'),
        ('accumulated_pe',
         'CHECK (accumulated_pe >= 0)',
         'The accumulated Pe value cannot be negative.'),
    ]

    @api.depends('cropunit_id', 'cropunit_id.name',
                 'monitoringperiod_id', 'monitoringperiod_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.monitoringperiod_id and record.cropunit_id:
                name = record.monitoringperiod_id.name + '-' + \
                       record.cropunit_id.name
            record.name = name

    @api.multi
    def _compute_kc(self):
        for record in self:
            kc = 0
            if record.cropunit_id.cultivation_id.suitable_hydric_estimation:
                cropfamily = record.cropunit_id.cultivation_id.cropfamily_id
                if cropfamily:
                    kc = cropfamily.calculate_kc(record.mean_ndvi)
            record.kc = kc

    @api.multi
    def _compute_accumulated_etc(self):
        for record in self:
            record.accumulated_etc = record.accumulated_et0 * record.kc

    @api.model
    def calculate_nin(self, accumulated_et0=0, accumulated_pe=0,
                      mean_ndvi=0, cultivation=None):
        nin = 0
        if (cultivation and cultivation.suitable_hydric_estimation and
           cultivation.cropfamily_id):
            kc = cultivation.cropfamily_id.calculate_kc(mean_ndvi)
            nin = 10 * ((accumulated_et0 * kc) - accumulated_pe)
            if nin < 0:
                nin = 0
        return nin

    @api.depends('nin', 'cropunit_id.standard_application_efficiency')
    def _compute_gin(self):
        for record in self:
            record.gin = (record.nin /
                          record.cropunit_id.standard_application_efficiency)

    @api.depends('gin', 'cropunit_id.area_gis_ha')
    def _compute_total_gin(self):
        for record in self:
            record.total_gin = record.gin * record.cropunit_id.area_gis_ha

    @api.depends('monitoringperiod_id')
    def _compute_initial_date(self):
        for record in self:
            initial_date = None
            if (record.monitoringperiod_id and
               record.monitoringperiod_id.initial_date):
                initial_date = record.monitoringperiod_id.initial_date
            record.initial_date = initial_date

    @api.depends('monitoringperiod_id')
    def _compute_end_date(self):
        for record in self:
            end_date = None
            if (record.monitoringperiod_id and
               record.monitoringperiod_id.end_date):
                end_date = record.monitoringperiod_id.end_date
            record.end_date = end_date

    @api.depends('cropunit_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.cropunit_id and record.cropunit_id.agriculturalseason_id:
                agriculturalseason_id = \
                    record.cropunit_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('cropunit_id')
    def _compute_parcel_id(self):
        for record in self:
            parcel_id = None
            if record.cropunit_id and record.cropunit_id.parcel_id:
                parcel_id = record.cropunit_id.parcel_id
            record.parcel_id = parcel_id

    @api.depends('cropunit_id', 'cropunit_id.cultivation_id')
    def _compute_cultivation_id(self):
        for record in self:
            cultivation_id = None
            if record.cropunit_id and record.cropunit_id.cultivation_id:
                cultivation_id = record.cropunit_id.cultivation_id
            record.cultivation_id = cultivation_id

    @api.depends('cropunit_id')
    def _compute_order_number(self):
        for record in self:
            order_number = 0
            if record.cropunit_id and record.cropunit_id.order_number:
                order_number = record.cropunit_id.order_number
            record.order_number = order_number

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.end_date)
            name = initial_date_str + ' - ' + end_date_str + \
                ', ' + record.cropunit_id.name
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        accumulated_et0 = 0
        accumulated_pe = 0
        mean_ndvi = 0
        if ('cropunit_id' in vals and vals['cropunit_id'] and
           'monitoringperiod_id' in vals and vals['monitoringperiod_id']):
            cropunit = self.env['wua.cropunit'].browse(vals['cropunit_id'])
            monitoringperiod = self.env['wua.monitoringperiod'].browse(
                vals['monitoringperiod_id'])
            if cropunit and monitoringperiod:
                accumulated_et0, accumulated_pe, mean_ndvi = \
                    self.get_parcel_data(cropunit.parcel_id, monitoringperiod)
                vals['accumulated_et0'] = accumulated_et0
                vals['accumulated_pe'] = accumulated_pe
                vals['mean_ndvi'] = mean_ndvi
                vals['nin'] = self.calculate_nin(accumulated_et0,
                                                 accumulated_pe,
                                                 mean_ndvi,
                                                 cropunit.cultivation_id)
        new_hydricneed = super(WuaHydricneed, self).create(vals)
        return new_hydricneed

    def get_parcel_data(self, parcel, monitoringperiod):
        accumulated_et0 = 0.0
        accumulated_pe = 0.0
        mean_ndvi = 0.0
        et0_sensor_type_id = self.env['ir.values'].get_default(
            'wua.configuration', 'hydric_est_et0_sensor_type')
        pe_sensor_type_id = self.env['ir.values'].get_default(
            'wua.configuration', 'hydric_est_pe_sensor_type')
        max_offset_alternative_ndvi = self.env['ir.values'].get_default(
            'wua.configuration', 'max_offset_alternative_ndvi')
        if not max_offset_alternative_ndvi:
            max_offset_alternative_ndvi = 0
        if et0_sensor_type_id and pe_sensor_type_id:
            model_sensor_reading = self.env['wua.parcel.sensor.reading']
            model_ndvi = self.env['wua.parcel.vegetationindex.ndvi']
            initial_date = str(monitoringperiod.initial_date)
            initial_datetime = initial_date + ' 00:00:00'
            end_date = str(monitoringperiod.end_date)
            end_datetime = end_date + ' 23:59:59'
            et0_sensor_readings = model_sensor_reading.search(
                [('parcel_id', '=', parcel.id),
                 ('type_id', '=', et0_sensor_type_id),
                 ('measurement_time', '>=', initial_datetime),
                 ('measurement_time', '<=', end_datetime)])
            for et0_sensor_reading in (et0_sensor_readings or []):
                accumulated_et0 = accumulated_et0 + et0_sensor_reading.value
            pe_sensor_readings = model_sensor_reading.search(
                [('parcel_id', '=', parcel.id),
                 ('type_id', '=', pe_sensor_type_id),
                 ('measurement_time', '>=', initial_datetime),
                 ('measurement_time', '<=', end_datetime)])
            for pe_sensor_reading in (pe_sensor_readings or []):
                accumulated_pe = accumulated_pe + pe_sensor_reading.value
            ndvi_values = model_ndvi.search(
                [('parcel_id', '=', parcel.id),
                 ('data_date', '>=', initial_date),
                 ('data_date', '<=', end_date)])
            if not ndvi_values and max_offset_alternative_ndvi > 0:
                initial_date_as_datetime = \
                    (datetime.datetime.strptime(str(initial_date), '%Y-%m-%d') -
                     datetime.timedelta(days=max_offset_alternative_ndvi))
                initial_date = datetime.datetime.strftime(
                    initial_date_as_datetime, '%Y-%m-%d')
                ndvi_values = model_ndvi.search(
                    [('parcel_id', '=', parcel.id),
                     ('data_date', '>=', initial_date),
                     ('data_date', '<=', end_date)])
            if ndvi_values:
                accumulated_ndvi_value = 0
                for ndvi_value in ndvi_values:
                    accumulated_ndvi_value = (accumulated_ndvi_value +
                                              ndvi_value.mean_value)
                mean_ndvi = accumulated_ndvi_value / len(ndvi_values)
        return accumulated_et0, accumulated_pe, mean_ndvi
