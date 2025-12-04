# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime

from odoo import models, fields, api, exceptions, _


class WuaHydricneed(models.Model):
    _name = 'wua.hydricneed'
    _description = 'Hydric needs of the crop units'
    _order = 'initial_date desc, name'

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
        string='Accumulated ETo',
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

    area_gis_ha = fields.Float(
        string='Crop Unit Area (ha)',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_gis_ha',
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

    cropfamily_id = fields.Many2one(
        string='Crop Family',
        comodel_name='wua.cropfamily',
        store=True,
        index=True,
        compute='_compute_cropfamily_id',
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

    mapped_to_active_agriculturalseason = fields.Boolean(
        string='Mapped to the active agricultural season',
        compute='_compute_mapped_to_active_agriculturalseason',
        search='_search_mapped_to_active_agriculturalseason',
    )

    is_occurred_or_current_controlperiod = fields.Boolean(
        string='Occurred or current control period (y/n)',
        compute='_compute_is_occurred_or_current_controlperiod',
        search='_search_is_occurred_or_current_controlperiod',
    )

    kc_function = fields.Char(
        string='Kc(ndvi)',
        compute='_compute_kc_function',
    )

    etc_function = fields.Char(
        string='ETc(Kc,ETo)',
        compute='_compute_etc_function',
    )

    nin_function = fields.Char(
        string='NIN(ETc,Pe)',
        compute='_compute_nin_function',
    )

    standard_application_efficiency = fields.Float(
        string='Standard Application Efficiency',
        compute='_compute_standard_application_efficiency',
    )

    gin_function = fields.Char(
        string='GIN(ETc,Pe)',
        compute='_compute_gin_function',
    )

    total_gin_function = fields.Char(
        string='Total GIN(GIN,A)',
        compute='_compute_total_gin_function',
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

    @api.depends('cropunit_id', 'cropunit_id.area_gis_ha')
    def _compute_area_gis_ha(self):
        for record in self:
            area_gis_ha = 0
            if record.cropunit_id and record.cropunit_id.area_gis_ha:
                area_gis_ha = record.cropunit_id.area_gis_ha
            record.area_gis_ha = area_gis_ha

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

    @api.depends('cultivation_id', 'cultivation_id.cropfamily_id')
    def _compute_cropfamily_id(self):
        for record in self:
            cropfamily_id = None
            if record.cultivation_id and record.cultivation_id.cropfamily_id:
                cropfamily_id = record.cultivation_id.cropfamily_id
            record.cropfamily_id = cropfamily_id

    @api.depends('cropunit_id')
    def _compute_order_number(self):
        for record in self:
            order_number = 0
            if record.cropunit_id and record.cropunit_id.order_number:
                order_number = record.cropunit_id.order_number
            record.order_number = order_number

    @api.multi
    def _compute_mapped_to_active_agriculturalseason(self):
        for record in self:
            mapped_to_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                mapped_to_active_agriculturalseason = True
            record.mapped_to_active_agriculturalseason = \
                mapped_to_active_agriculturalseason

    def _search_mapped_to_active_agriculturalseason(self, operator, value):
        hydricneed_ids = []
        filter_operator = 'in'
        mapped_to_active_agriculturalseason = \
            ((operator == '=' and value) or (operator == '!=' and not value))
        id_of_active_agriculturalseason = 0
        active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            id_of_active_agriculturalseason = active_agriculturalseason[0].id
        sql_statement = \
            ('SELECT id FROM wua_hydricneed WHERE agriculturalseason_id = '
             '%s' % (id_of_active_agriculturalseason, ))
        if not mapped_to_active_agriculturalseason:
            sql_statement = \
                ('SELECT id FROM wua_hydricneed WHERE agriculturalseason_id <> '
                 '%s' % (id_of_active_agriculturalseason,))
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                hydricneed_ids.append(item[0])
        return [('id', filter_operator, hydricneed_ids)]

    @api.multi
    def _compute_is_occurred_or_current_controlperiod(self):
        current_date = datetime.date.today()
        for record in self:
            is_occurred_or_current_controlperiod = False
            initial_date = fields.Date.from_string(record.initial_date)
            if current_date >= initial_date:
                is_occurred_or_current_controlperiod = True
            record.is_occurred_or_current_controlperiod = \
                is_occurred_or_current_controlperiod

    def _search_is_occurred_or_current_controlperiod(self, operator, value):
        hydricneed_ids = []
        filter_operator = 'in'
        is_occurred_or_current_controlperiod =\
            ((operator == '=' and value) or (operator == '!=' and not value))
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        sql_statement = ('SELECT id FROM wua_hydricneed '
                         'WHERE initial_date <= \'%s\'' % (current_date,))
        if not is_occurred_or_current_controlperiod:
            sql_statement = ('SELECT id FROM wua_hydricneed '
                             'WHERE initial_date > \'%s\'' % (current_date,))
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                hydricneed_ids.append(item[0])
        return [('id', filter_operator, hydricneed_ids)]

    @api.multi
    def _compute_kc_function(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            kc_function = ''
            if record.mean_ndvi and record.cropfamily_id:
                mean_ndvi_str = model_transform.transform_float_to_locale(
                    record.mean_ndvi, 4)
                kc_a_str = model_transform.transform_float_to_locale(
                    record.cropfamily_id.kc_a, 4)
                kc_b_str = model_transform.transform_float_to_locale(
                    record.cropfamily_id.kc_b, 4)
                kc_c_str = model_transform.transform_float_to_locale(
                    record.cropfamily_id.kc_c, 4)
                kc_str = model_transform.transform_float_to_locale(
                    record.kc, 4)
                kc_function = \
                    _('Kc(NDVI)') + ' = ' + \
                    kc_a_str + u' · ' + mean_ndvi_str + u' ² + ' + \
                    kc_b_str + u' · ' + mean_ndvi_str + ' + ' + \
                    kc_c_str + ' = ' + kc_str
            record.kc_function = kc_function

    @api.multi
    def _compute_etc_function(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            accumulated_et0_str = model_transform.transform_float_to_locale(
                record.accumulated_et0, 4)
            kc_str = model_transform.transform_float_to_locale(
                record.kc, 4)
            accumulated_etc_str = model_transform.transform_float_to_locale(
                record.accumulated_etc, 4)
            record.etc_function = \
                _('ETc(Kc, ETo)') + ' = ' + \
                kc_str + u' · ' + accumulated_et0_str + ' = ' + \
                accumulated_etc_str

    @api.multi
    def _compute_nin_function(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            accumulated_etc_str = model_transform.transform_float_to_locale(
                record.accumulated_etc, 4)
            accumulated_pe_str = model_transform.transform_float_to_locale(
                record.accumulated_pe, 4)
            nin_str = model_transform.transform_float_to_locale(
                record.nin, 2)
            record.nin_function = \
                _('NIN(ETc, Pe)') + ' = 10' + u' · ' + \
                '(' + accumulated_etc_str + ' - ' + \
                accumulated_pe_str + ')' + ' = ' + \
                nin_str

    @api.multi
    def _compute_standard_application_efficiency(self):
        for record in self:
            standard_application_efficiency = 1
            if (record.cropunit_id and
               record.cropunit_id.standard_application_efficiency > 0):
                standard_application_efficiency = \
                    record.cropunit_id.standard_application_efficiency
            record.standard_application_efficiency = \
                standard_application_efficiency * 100

    @api.multi
    def _compute_gin_function(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            nin_str = model_transform.transform_float_to_locale(
                record.nin, 2)
            sae_str = model_transform.transform_float_to_locale(
                record.standard_application_efficiency / 100, 2)
            gin_str = model_transform.transform_float_to_locale(
                record.gin, 2)
            record.gin_function = \
                _('GIN(NIN, SAE)') + ' = ' + nin_str + ' / ' + \
                sae_str + ' = ' + gin_str

    @api.multi
    def _compute_total_gin_function(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            gin_str = model_transform.transform_float_to_locale(
                record.gin, 2)
            area_gis_ha_str = model_transform.transform_float_to_locale(
                record.area_gis_ha, 4)
            total_gin_str = model_transform.transform_float_to_locale(
                record.total_gin, 2)
            record.total_gin_function = \
                _('Total GIN(GIN, A)') + ' = ' + gin_str + u' · ' + \
                area_gis_ha_str + ' = ' + total_gin_str

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
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'order_number' in fields:
            fields.remove('order_number')
        if 'mean_ndvi' in fields:
            fields.remove('mean_ndvi')
        if 'nin' in fields:
            fields.remove('nin')
        if 'gin' in fields:
            fields.remove('gin')
        return super(WuaHydricneed, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

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
