# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _
import string


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    _infrastructure_items = ['waterconnection_id', 'watermeter_id',
                             'irrigationshed_id', 'pressuresensor_id',
                             'waterpipe_id']

    tag_ids = fields.Many2many(
        string='Equipment Tags',
        comodel_name='maintenance.equipmenttag',
        relation='equipment_tag_rel',
        column1='equipment_id', column2='tag_id')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        compute='_compute_hydraulicsector',
        store=False)

    is_wua = fields.Boolean(compute='_compute_is_wua', store=True)

    infrastructure_type = fields.Selection(
        selection=[
            ('01_general', 'General Infrastructure'),
            ('02_pressurized', 'Pressurized Irrigation'),
            ('03_gravity', 'Gravity Irrigation')
        ],
        compute='_compute_infrastructure_type',
        store=True
    )

    is_primary = fields.Boolean(compute='_compute_is_primary',
                                store=True)

    active = fields.Boolean(default=True)

    intake_ids = fields.One2many(
        string='Intakes',
        comodel_name='wua.intake',
        inverse_name='equipment_id')

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        compute='_compute_intake_id',)

    reservoir_ids = fields.One2many(
        string='Reservoirs',
        comodel_name='wua.reservoir',
        inverse_name='equipment_id',)

    reservoir_id = fields.Many2one(
        string='Reservoir',
        comodel_name='wua.reservoir',
        compute='_compute_reservoir_id',)

    pumpgroup_ids = fields.One2many(
        string='pumpgroups',
        comodel_name='wua.pumpgroup',
        inverse_name='equipment_id',)

    pumpgroup_id = fields.Many2one(
        string='pumpgroup',
        comodel_name='wua.pumpgroup',
        compute='_compute_pumpgroup_id',)

    photovoltaicplant_ids = fields.One2many(
        string='photovoltaicplants',
        comodel_name='wua.photovoltaicplant',
        inverse_name='equipment_id',)

    photovoltaicplant_id = fields.Many2one(
        string='photovoltaicplant',
        comodel_name='wua.photovoltaicplant',
        compute='_compute_photovoltaicplant_id',)

    flowmeter_ids = fields.One2many(
        string='flowmeters',
        comodel_name='wua.flowmeter',
        inverse_name='equipment_id',)

    flowmeter_id = fields.Many2one(
        string='flowmeter',
        comodel_name='wua.flowmeter',
        compute='_compute_flowmeter_id',)

    pumpunit_ids = fields.One2many(
        string='pumps',
        comodel_name='wua.pumpunit',
        inverse_name='equipment_id',)

    pumpunit_id = fields.Many2one(
        string='pump',
        comodel_name='wua.pumpunit',
        compute='_compute_pumpunit_id',)

    waterpipe_ids = fields.One2many(
        string='waterpipes',
        comodel_name='wua.waterpipe',
        inverse_name='equipment_id',)

    waterpipe_id = fields.Many2one(
        string='waterpipe',
        comodel_name='wua.waterpipe',
        compute='_compute_waterpipe_id',)

    irrigationshed_ids = fields.One2many(
        string='irrigationsheds',
        comodel_name='wua.irrigationshed',
        inverse_name='equipment_id',)

    irrigationshed_id = fields.Many2one(
        string='irrigationshed',
        comodel_name='wua.irrigationshed',
        compute='_compute_irrigationshed_id',)

    waterconnection_ids = fields.One2many(
        string='waterconnections',
        comodel_name='wua.waterconnection',
        inverse_name='equipment_id',)

    waterconnection_id = fields.Many2one(
        string='waterconnection',
        comodel_name='wua.waterconnection',
        compute='_compute_waterconnection_id',)

    watermeter_ids = fields.One2many(
        string='watermeters',
        comodel_name='wua.watermeter',
        inverse_name='equipment_id',)

    watermeter_id = fields.Many2one(
        string='watermeter',
        comodel_name='wua.watermeter',
        compute='_compute_watermeter_id',)

    pressuresensor_ids = fields.One2many(
        string='pressuresensors',
        comodel_name='wua.pressuresensor',
        inverse_name='equipment_id',)

    pressuresensor_id = fields.Many2one(
        string='pressuresensor',
        comodel_name='wua.pressuresensor',
        compute='_compute_pressuresensor_id',)

    irrigationditch_ids = fields.One2many(
        string='irrigationditchs',
        comodel_name='wua.irrigationditch',
        inverse_name='equipment_id',)

    irrigationditch_id = fields.Many2one(
        string='irrigationditch',
        comodel_name='wua.irrigationditch',
        compute='_compute_irrigationditch_id',)

    drainageditch_ids = fields.One2many(
        string='drainageditchs',
        comodel_name='wua.drainageditch',
        inverse_name='equipment_id',)

    drainageditch_id = fields.Many2one(
        string='drainageditch',
        comodel_name='wua.drainageditch',
        compute='_compute_drainageditch_id',)

    flowdivider_ids = fields.One2many(
        string='flowdividers',
        comodel_name='wua.flowdivider',
        inverse_name='equipment_id',)

    flowdivider_id = fields.Many2one(
        string='flowdivider',
        comodel_name='wua.flowdivider',
        compute='_compute_flowdivider_id',)

    irrigationgate_ids = fields.One2many(
        string='irrigationgates',
        comodel_name='wua.irrigationgate',
        inverse_name='equipment_id',)

    irrigationgate_id = fields.Many2one(
        string='irrigationgate',
        comodel_name='wua.irrigationgate',
        compute='_compute_irrigationgate_id',)

    airvalve_ids = fields.One2many(
        string='airvalves',
        comodel_name='wua.airvalve',
        inverse_name='equipment_id',)

    airvalve_id = fields.Many2one(
        string='airvalve',
        comodel_name='wua.airvalve',
        compute='_compute_airvalve_id',)

    drainagevalve_ids = fields.One2many(
        string='drainagevalves',
        comodel_name='wua.drainagevalve',
        inverse_name='equipment_id',)

    drainagevalve_id = fields.Many2one(
        string='drainagevalve',
        comodel_name='wua.drainagevalve',
        compute='_compute_drainagevalve_id',)

    valve_ids = fields.One2many(
        string='valves',
        comodel_name='wua.valve',
        inverse_name='equipment_id',)

    valve_id = fields.Many2one(
        string='valve',
        comodel_name='wua.valve',
        compute='_compute_valve_id',)

    filteringstation_ids = fields.One2many(
        string='filteringstations',
        comodel_name='wua.filteringstation',
        inverse_name='equipment_id',)

    filteringstation_id = fields.Many2one(
        string='filteringstation',
        comodel_name='wua.filteringstation',
        compute='_compute_filteringstation_id',)

    tag_html = fields.Html(string="Tag HTML", compute='_compute_tag_html')

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    @api.multi
    def _compute_hydraulicsector(self):
        attributes_to_check = [
            'waterconnection_id',
            'watermeter_id',
            'irrigationshed_id',
            'pressuresensor_id',
            'waterpipe_id',
            'airvalve_id',
            'valve_id',
            'drainagevalve_id',
            'filteringstation_id'
        ]
        for record in self:
            hydraulicsector_id = None
            for attr in attributes_to_check:
                related_record = getattr(record, attr, None)
                if related_record and related_record.hydraulicsector_id:
                    hydraulicsector_id = related_record.hydraulicsector_id
                    break
            record.hydraulicsector_id = hydraulicsector_id

    @api.depends('category_id', 'category_id.is_wua')
    def _compute_is_wua(self):
        for record in self:
            record.is_wua = record.category_id.is_wua

    @api.depends('category_id', 'category_id.infrastructure_type')
    def _compute_infrastructure_type(self):
        for record in self:
            record.infrastructure_type = record.category_id.infrastructure_type

    @api.depends('category_id', 'category_id.is_primary')
    def _compute_is_primary(self):
        for record in self:
            record.is_primary = record.category_id.is_primary

    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if record.intake_ids:
                intake_id = record.intake_ids[0]
            record.intake_id = intake_id

    def _compute_reservoir_id(self):
        for record in self:
            reservoir_id = None
            if record.reservoir_ids:
                reservoir_id = record.reservoir_ids[0]
            record.reservoir_id = reservoir_id

    def _compute_watermeter_id(self):
        for record in self:
            watermeter_id = None
            if record.watermeter_ids:
                watermeter_id = record.watermeter_ids[0]
            record.watermeter_id = watermeter_id

    def _compute_pumpgroup_id(self):
        for record in self:
            pumpgroup_id = None
            if record.pumpgroup_ids:
                pumpgroup_id = record.pumpgroup_ids[0]
            record.pumpgroup_id = pumpgroup_id

    def _compute_photovoltaicplant_id(self):
        for record in self:
            photovoltaicplant_id = None
            if record.photovoltaicplant_ids:
                photovoltaicplant_id = record.photovoltaicplant_ids[0]
            record.photovoltaicplant_id = photovoltaicplant_id

    def _compute_flowmeter_id(self):
        for record in self:
            flowmeter_id = None
            if record.flowmeter_ids:
                flowmeter_id = record.flowmeter_ids[0]
            record.flowmeter_id = flowmeter_id

    def _compute_pumpunit_id(self):
        for record in self:
            pumpunit_id = None
            if record.pumpunit_ids:
                pumpunit_id = record.pumpunit_ids[0]
            record.pumpunit_id = pumpunit_id

    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if record.waterpipe_ids:
                waterpipe_id = record.waterpipe_ids[0]
            record.waterpipe_id = waterpipe_id

    def _compute_waterconnection_id(self):
        for record in self:
            waterconnection_id = None
            if record.waterconnection_ids:
                waterconnection_id = record.waterconnection_ids[0]
            record.waterconnection_id = waterconnection_id

    def _compute_irrigationshed_id(self):
        for record in self:
            irrigationshed_id = None
            if record.irrigationshed_ids:
                irrigationshed_id = record.irrigationshed_ids[0]
            record.irrigationshed_id = irrigationshed_id

    def _compute_pressuresensor_id(self):
        for record in self:
            pressuresensor_id = None
            if record.pressuresensor_ids:
                pressuresensor_id = record.pressuresensor_ids[0]
            record.pressuresensor_id = pressuresensor_id

    def _compute_irrigationditch_id(self):
        for record in self:
            irrigationditch_id = None
            if record.irrigationditch_ids:
                irrigationditch_id = record.irrigationditch_ids[0]
            record.irrigationditch_id = irrigationditch_id

    def _compute_drainageditch_id(self):
        for record in self:
            drainageditch_id = None
            if record.drainageditch_ids:
                drainageditch_id = record.drainageditch_ids[0]
            record.drainageditch_id = drainageditch_id

    def _compute_flowdivider_id(self):
        for record in self:
            flowdivider_id = None
            if record.flowdivider_ids:
                flowdivider_id = record.flowdivider_ids[0]
            record.flowdivider_id = flowdivider_id

    def _compute_irrigationgate_id(self):
        for record in self:
            irrigationgate_id = None
            if record.irrigationgate_ids:
                irrigationgate_id = record.irrigationgate_ids[0]
            record.irrigationgate_id = irrigationgate_id

    def _compute_airvalve_id(self):
        for record in self:
            airvalve_id = None
            if record.airvalve_ids:
                airvalve_id = record.airvalve_ids[0]
            record.airvalve_id = airvalve_id

    def _compute_valve_id(self):
        for record in self:
            valve_id = None
            if record.valve_ids:
                valve_id = record.valve_ids[0]
            record.valve_id = valve_id

    def _compute_drainagevalve_id(self):
        for record in self:
            drainagevalve_id = None
            if record.drainagevalve_ids:
                drainagevalve_id = record.drainagevalve_ids[0]
            record.drainagevalve_id = drainagevalve_id

    def _compute_filteringstation_id(self):
        for record in self:
            filteringstation_id = None
            if record.filteringstation_ids:
                filteringstation_id = record.filteringstation_ids[0]
            record.filteringstation_id = filteringstation_id

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.is_wua:
                name = name + ' (' +\
                    string.capwords(record.category_id.name) + ')'
            result.append((record.id, name))
        return result

    @api.multi
    def action_get_wua_infrastructure_item(self):
        self.ensure_one()
        current_equipment = self

        category_mapping = {
            'wua_maintenance.equipment_category_intake':
                ('wua.intake', _('Intake')),
            'wua_maintenance.equipment_category_reservoir':
                ('wua.reservoir', _('Reservoir')),
            'wua_maintenance.equipment_category_pumpgroup':
                ('wua.pumpgroup', _('pumpgroup')),
            'wua_maintenance.equipment_category_photovoltaicplant':
                ('wua.photovoltaicplant', _('photovoltaicplant')),
            'wua_maintenance.equipment_category_flowmeter':
                ('wua.flowmeter', _('flowmeter')),
            'wua_maintenance.equipment_category_pump':
                ('wua.pumpunit', _('pump')),
            'wua_maintenance.equipment_category_waterpipe':
                ('wua.waterpipe', _('waterpipe')),
            'wua_maintenance.equipment_category_irrigationshed':
                ('wua.irrigationshed', _('irrigationshed')),
            'wua_maintenance.equipment_category_waterconnection':
                ('wua.waterconnection', _('waterconnection')),
            'wua_maintenance.equipment_category_watermeter':
                ('wua.watermeter', _('watermeter')),
            'wua_maintenance.equipment_category_pressuresensor':
                ('wua.pressuresensor', _('pressuresensor')),
            'wua_maintenance.equipment_category_irrigationditch':
                ('wua.irrigationditch', _('irrigationditch')),
            'wua_maintenance.equipment_category_drainageditch':
                ('wua.drainageditch', _('drainageditch')),
            'wua_maintenance.equipment_category_flowdivider':
                ('wua.flowdivider', _('flowdivider')),
            'wua_maintenance.equipment_category_irrigationgate':
                ('wua.irrigationgate', _('irrigationgate')),
            'wua_maintenance.equipment_category_airvalve':
                ('wua.airvalve', _('airvalve')),
            'wua_maintenance.equipment_category_valve':
                ('wua.valve', _('valve')),
            'wua_maintenance.equipment_category_drainagevalve':
                ('wua.drainagevalve', _('drainagevalve')),
            'wua_maintenance.equipment_category_filteringstation':
                ('wua.filteringstation', _('filteringstation'))
        }

        res_model, name = category_mapping.get(current_equipment.category_id, (None, None))

        if not res_model:
            raise exceptions.UserError(_('Equipment No-WUA.'))

        domain = [('equipment_id', '=', current_equipment.id)]
        if not self.active:
            domain.append(('active', '=', False))

        res_id = self.env[res_model].search(domain, limit=1).id

        if not res_id:
            raise exceptions.UserError(_('Equipment No-WUA.'))

        act_window = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'form',
            'res_id': res_id,
            'context': {'create': False},
        }
        return act_window

