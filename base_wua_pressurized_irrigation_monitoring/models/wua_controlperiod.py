# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from datetime import timedelta
from odoo import models, fields, api, _, exceptions


class WuaControlperiod(models.Model):
    _name = 'wua.controlperiod'
    _description = 'Entity (control period)'
    _order = 'name'

    # Size of fields "name" and "description".
    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 75

    name = fields.Char(
        string='Control Period',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated')
        ],
        default='draft',
        string='Controlperiod Status',
    )

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True
    )

    end_date = fields.Date(
        string='End Date',
        default=lambda self: fields.datetime.now() + timedelta(days=7),
        required=True,
        index=True
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='cascade',
        required=True
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

    notes = fields.Html(
        string='Notes'
    )

    controlpresconsumption_ids = fields.One2many(
        string="Control Presconsumption",
        comodel_name="wua.controlpresconsumption",
        inverse_name="controlperiod_id"
    )

    subparcel_presconsumption_ids = fields.One2many(
        string="Comparative Subparcel Presconsumption",
        comodel_name="wua.comparative.subparcel.presconsumption",
        inverse_name="controlperiod_id"
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.estimated_consumption')
    def _compute_estimated_consumption(self):
        for record in self:
            estimated_consumption = 0
            for subp_pres in record.subparcel_presconsumption_ids:
                estimated_consumption += subp_pres.estimated_consumption
            record.estimated_consumption = estimated_consumption

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.real_consumption')
    def _compute_real_consumption(self):
        for record in self:
            real_consumption = 0
            for subp_pres in record.subparcel_presconsumption_ids:
                real_consumption += subp_pres.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1 and
           ((self.initial_date < self.agriculturalseason_id.initial_date) or
           (self.end_date > self.agriculturalseason_id.end_date))):
            raise exceptions.ValidationError(_(
                'The control period limits are outside the agricultural '
                'season.'))

    @api.constrains('initial_date', 'end_date')
    def _check_others_controlperiods(self):
        controlperiods = self.env['wua.controlperiod'].search(
            ['&', ('initial_date', '<=', self.end_date),
             ('end_date', '>=', self.initial_date)])
        if (len(self) == 1 and len(controlperiods) > 1):
            raise exceptions.ValidationError(_(
                'The control period overlaps with another.'))

    @api.model
    def create(self, vals):
        new_controlperiod = super(WuaControlperiod, self).create(vals)
        ctrl_pres = self.env['wua.controlpresconsumption'].search(
            ['&', ('reading_end_time', '<=', new_controlperiod.end_date),
             ('reading_initial_time', '>=', new_controlperiod.initial_date)])
        if (len(ctrl_pres) > 0):
            ctrl_pres.write({
                'controlperiod_id': new_controlperiod.id
            })
        filtered_subparcels = self.env['wua.parcel.subparcel'].search(
            [('cultivation_id.monitoring', '=', True)])
        if len(filtered_subparcels) > 0:
            comp_subp_presc = \
                self.env['wua.comparative.subparcel.presconsumption']
            for subparcel in filtered_subparcels:
                comp_subp_presc.create({
                    'subparcel_id': subparcel.id,
                    'parcel_id': subparcel.parcel_id.id,
                    'cadastral_reference':
                        subparcel.parcel_id.cadastral_reference,
                    'area_perc': subparcel.area_perc,
                    'irrigationsystem_id': subparcel.irrigationsystem_id.id,
                    'tree_distance': subparcel.tree_distance,
                    'tree_development': subparcel.tree_development,
                    'tree_lateral_number': subparcel.tree_lateral_number,
                    'tree_drippers_number': subparcel.tree_drippers_number,
                    'row_distance': subparcel.row_distance,
                    'controlperiod_id': new_controlperiod.id,
                    'partner_id': subparcel.partner_id.id,
                    'hydraulicsector_id': subparcel.hydraulicsector_id.id,
                    'cultivation_id': subparcel.cultivation_id.id,
                    'cultivationvariety_id':
                        subparcel.cultivationvariety_id.id,
                    'area_official': subparcel.area_official,
                    'productionmethod_id': subparcel.productionmethod_id.id,
                    'shaded_percentage': subparcel.shaded_percentage,
                    'soil_type': subparcel.soil_type,
                    'organic_material_percentage':
                        subparcel.organic_material_percentage,
                    'orientation': subparcel.orientation,
                    'drippers_number': subparcel.drippers_number,
                    'drippers_nomial_flow': subparcel.drippers_nomial_flow
                    })
        return new_controlperiod

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def calculate_controlperiod(self):
        for record in self:
            if (record.subparcel_presconsumption_ids):
                # TODO: Future implementation
                for subparcel in record.subparcel_presconsumption_ids:
                    subparcel.estimated_consumption = 0
            record.state = 'calculated'

    @api.multi
    def cancel_controlperiod(self):
        for record in self:
            if (record.subparcel_presconsumption_ids):
                for subparcel in record.subparcel_presconsumption_ids:
                    subparcel.estimated_consumption = 0
            record.state = 'draft'

    def get_wua_controlperiod_comparative_presconsumption_action(self):
        current_controlperiod_id = self.env.context.get('active_id')
        condition = [('controlperiod_id', '=', current_controlperiod_id)]
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
            }
        return act_window

    def get_wua_controlperiod_control_presconsumption_action(self):
        current_controlperiod_id = self.env.context.get('active_id')
        condition = [('controlperiod_id', '=', current_controlperiod_id)]
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
            'name': _('Control Presconsumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': self.env.context,
            }
        return act_window
