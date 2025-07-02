# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _
from datetime import timedelta
import string


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    _infrastructure_items = ['waterconnection_id', 'watermeter_id',
                             'irrigationshed_id', 'pressuresensor_id',
                             'waterpipe_id']

    name = fields.Char(
        translate=False,
    )

    tag_ids = fields.Many2many(
        string='Equipment Tags',
        comodel_name='maintenance.equipmenttag',
        relation='equipment_tag_rel',
        column1='equipment_id',
        column2='tag_id',
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        compute='_compute_hydraulicsector',
        store=False,
    )

    is_wua = fields.Boolean(
        string='Is WUA',
        compute='_compute_is_wua',
        store=True,
    )

    infrastructure_type = fields.Selection(
        selection=[
            ('01_general', 'General Infrastructure'),
            ('02_pressurized', 'Pressurized Irrigation'),
            ('03_gravity', 'Gravity Irrigation'),
        ],
        compute='_compute_infrastructure_type',
        store=True,
    )

    is_primary = fields.Boolean(
        string='Is Primary',
        compute='_compute_is_primary',
        store=True,
    )

    intake_ids = fields.One2many(
        string='Intakes',
        comodel_name='wua.intake',
        inverse_name='equipment_id',
    )

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        compute='_compute_intake_id',
    )

    reservoir_ids = fields.One2many(
        string='Reservoirs',
        comodel_name='wua.reservoir',
        inverse_name='equipment_id',
    )

    reservoir_id = fields.Many2one(
        string='Reservoir',
        comodel_name='wua.reservoir',
        compute='_compute_reservoir_id',
    )

    pumpgroup_ids = fields.One2many(
        string='pumpgroups',
        comodel_name='wua.pumpgroup',
        inverse_name='equipment_id',
    )

    pumpgroup_id = fields.Many2one(
        string='pumpgroup',
        comodel_name='wua.pumpgroup',
        compute='_compute_pumpgroup_id',
    )

    photovoltaicplant_ids = fields.One2many(
        string='photovoltaicplants',
        comodel_name='wua.photovoltaicplant',
        inverse_name='equipment_id',
    )

    photovoltaicplant_id = fields.Many2one(
        string='photovoltaicplant',
        comodel_name='wua.photovoltaicplant',
        compute='_compute_photovoltaicplant_id',
    )

    flowmeter_ids = fields.One2many(
        string='flowmeters',
        comodel_name='wua.flowmeter',
        inverse_name='equipment_id',
    )

    flowmeter_id = fields.Many2one(
        string='flowmeter',
        comodel_name='wua.flowmeter',
        compute='_compute_flowmeter_id',
    )

    pumpunit_ids = fields.One2many(
        string='pumps',
        comodel_name='wua.pumpunit',
        inverse_name='equipment_id',
    )

    pumpunit_id = fields.Many2one(
        string='pump',
        comodel_name='wua.pumpunit',
        compute='_compute_pumpunit_id',
    )

    waterpipe_ids = fields.One2many(
        string='waterpipes',
        comodel_name='wua.waterpipe',
        inverse_name='equipment_id',
    )

    waterpipe_id = fields.Many2one(
        string='waterpipe',
        comodel_name='wua.waterpipe',
        compute='_compute_waterpipe_id',
    )

    irrigationshed_ids = fields.One2many(
        string='irrigationsheds',
        comodel_name='wua.irrigationshed',
        inverse_name='equipment_id',
    )

    irrigationshed_id = fields.Many2one(
        string='irrigationshed',
        comodel_name='wua.irrigationshed',
        compute='_compute_irrigationshed_id',
    )

    waterconnection_ids = fields.One2many(
        string='waterconnections',
        comodel_name='wua.waterconnection',
        inverse_name='equipment_id',
    )

    waterconnection_id = fields.Many2one(
        string='waterconnection',
        comodel_name='wua.waterconnection',
        compute='_compute_waterconnection_id',
    )

    watermeter_ids = fields.One2many(
        string='watermeters',
        comodel_name='wua.watermeter',
        inverse_name='equipment_id',
    )

    watermeter_id = fields.Many2one(
        string='watermeter',
        comodel_name='wua.watermeter',
        compute='_compute_watermeter_id',
    )

    pressuresensor_ids = fields.One2many(
        string='pressuresensors',
        comodel_name='wua.pressuresensor',
        inverse_name='equipment_id',
    )

    pressuresensor_id = fields.Many2one(
        string='pressuresensor',
        comodel_name='wua.pressuresensor',
        compute='_compute_pressuresensor_id',
    )

    irrigationditch_ids = fields.One2many(
        string='irrigationditchs',
        comodel_name='wua.irrigationditch',
        inverse_name='equipment_id',
    )

    irrigationditch_id = fields.Many2one(
        string='irrigationditch',
        comodel_name='wua.irrigationditch',
        compute='_compute_irrigationditch_id',
    )

    drainageditch_ids = fields.One2many(
        string='drainageditchs',
        comodel_name='wua.drainageditch',
        inverse_name='equipment_id',
    )

    drainageditch_id = fields.Many2one(
        string='drainageditch',
        comodel_name='wua.drainageditch',
        compute='_compute_drainageditch_id',
    )

    flowdivider_ids = fields.One2many(
        string='flowdividers',
        comodel_name='wua.flowdivider',
        inverse_name='equipment_id',
    )

    flowdivider_id = fields.Many2one(
        string='flowdivider',
        comodel_name='wua.flowdivider',
        compute='_compute_flowdivider_id',
    )

    irrigationgate_ids = fields.One2many(
        string='irrigationgates',
        comodel_name='wua.irrigationgate',
        inverse_name='equipment_id',
    )

    irrigationgate_id = fields.Many2one(
        string='irrigationgate',
        comodel_name='wua.irrigationgate',
        compute='_compute_irrigationgate_id',
    )

    airvalve_ids = fields.One2many(
        string='airvalves',
        comodel_name='wua.airvalve',
        inverse_name='equipment_id',
    )

    airvalve_id = fields.Many2one(
        string='airvalve',
        comodel_name='wua.airvalve',
        compute='_compute_airvalve_id',
    )

    drainagevalve_ids = fields.One2many(
        string='drainagevalves',
        comodel_name='wua.drainagevalve',
        inverse_name='equipment_id',
    )

    drainagevalve_id = fields.Many2one(
        string='drainagevalve',
        comodel_name='wua.drainagevalve',
        compute='_compute_drainagevalve_id',
    )

    valve_ids = fields.One2many(
        string='valves',
        comodel_name='wua.valve',
        inverse_name='equipment_id',
    )

    valve_id = fields.Many2one(
        string='valve',
        comodel_name='wua.valve',
        compute='_compute_valve_id',
    )

    filteringstation_ids = fields.One2many(
        string='filteringstations',
        comodel_name='wua.filteringstation',
        inverse_name='equipment_id',
    )

    filteringstation_id = fields.Many2one(
        string='filteringstation',
        comodel_name='wua.filteringstation',
        compute='_compute_filteringstation_id',
    )

    processingcentre_ids = fields.One2many(
        string='processingcentres',
        comodel_name='wua.processingcentre',
        inverse_name='equipment_id',
    )

    processingcentre_id = fields.Many2one(
        string='processingcentre',
        comodel_name='wua.processingcentre',
        compute='_compute_processingcentre_id',
    )

    powerline_ids = fields.One2many(
        string='powerlines',
        comodel_name='wua.powerline',
        inverse_name='equipment_id',
    )

    powerline_id = fields.Many2one(
        string='powerline',
        comodel_name='wua.powerline',
        compute='_compute_powerline_id',
    )

    powerlinesupport_ids = fields.One2many(
        string='powerlinesupports',
        comodel_name='wua.powerlinesupport',
        inverse_name='equipment_id',
    )

    powerlinesupport_id = fields.Many2one(
        string='powerlinesupport',
        comodel_name='wua.powerlinesupport',
        compute='_compute_powerlinesupport_id',
    )

    tag_html = fields.Html(
        string="Tag HTML",
        compute='_compute_tag_html',
    )

    image = fields.Binary(
        string='Photo / Image',
        attachment=True,
    )

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to '
        'hide the register without removing it. For see archived register, '
        'go to "Search-Filters" in tree view',
    )

    parent_id = fields.Many2one(
        string='Parent Equipment',
        comodel_name='maintenance.equipment',
        ondelete='set null',
    )

    child_ids = fields.One2many(
        string='Child Equipments',
        comodel_name='maintenance.equipment',
        inverse_name='parent_id',
    )

    description = fields.Html(
        string='Description',
    )

    with_infrastructure_gis = fields.Boolean(
        string='With Infrastructure GIS',
        default=False,
    )

    geojson_geom = fields.Text(
        string='GeoJSON Geometry',
    )

    building_ids = fields.One2many(
        string='Buildings',
        comodel_name='wua.building',
        inverse_name='equipment_id',
    )

    building_id = fields.Many2one(
        string='Building',
        comodel_name='wua.building',
        compute='_compute_building_id',
    )

    @api.constrains('category_id', 'parent_id')
    def _check_parent_category_consistency(self):
        for record in self:
            if record.category_id and record.parent_id and \
                    record.parent_id.category_id:
                expected_parent_category = record.category_id.parent_id
                actual_parent_category = record.parent_id.category_id
                if expected_parent_category and \
                        expected_parent_category != actual_parent_category:
                    raise exceptions.ValidationError(_(
                        "The category of the parent does not equals to "
                        "the parent category of %s.",
                    ) % (
                        record.category_id.display_name,
                    ))

    def write(self, vals):
        if 'geojson_geom' in vals and vals['geojson_geom']:
            # If the geojson_geom is set, we need to update the
            # with_infrastructure_gis field to True
            vals['with_infrastructure_gis'] = True
        res = super(MaintenanceEquipment, self).write(vals)
        return res

    def _get_category_table_mapping(self):
        env = self.env
        category_mapping = {
            env.ref('wua_maintenance.equipment_category_intake').id: {
                'base_table': 'wua_intake',
                'base_field': 'intake_code',
                'gis_table': 'wua_gis_intake',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref('wua_maintenance.equipment_category_reservoir').id: {
                'base_table': 'wua_reservoir',
                'base_field': 'reservoir_code',
                'gis_table': 'wua_gis_reservoir',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref('wua_maintenance.equipment_category_pumpgroup').id: {
                'base_table': 'wua_pumpgroup',
                'base_field': 'pumpgroup_code',
                'gis_table': 'wua_gis_pumpgroup',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_photovoltaicplant').id: {
                'base_table': 'wua_photovoltaicplant',
                'base_field': 'photovoltaicplant_code',
                'gis_table': 'wua_gis_photovoltaicplant',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref('wua_maintenance.equipment_category_flowmeter').id: {
                'base_table': 'wua_flowmeter',
                'base_field': 'name',
                'gis_table': 'wua_gis_flowmeter',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref('wua_maintenance.equipment_category_pump').id:  {
                'base_table': 'wua_pumpunit',
                'base_field': 'pumpgroup_id',
                'gis_table': 'wua_gis_pumpgroup',
                'gis_field': 'code',
                'intermediate_table': 'wua_pumpgroup',
                'intermediate_field': 'id',
                'intermediate_gis_field': 'pumpgroup_code',
            },
            env.ref('wua_maintenance.equipment_category_waterpipe').id: {
                'base_table': 'wua_waterpipe',
                'base_field': 'waterpipe_code',
                'gis_table': 'wua_gis_waterpipe',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_irrigationshed').id: {
                'base_table': 'wua_irrigationshed',
                'base_field': 'name',
                'gis_table': 'wua_gis_irrigationshed',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_waterconnection').id: {
                'base_table': 'wua_waterconnection',
                'base_field': 'irrigationshed_id',
                'gis_table': 'wua_gis_irrigationshed',
                'gis_field': 'name',
                'intermediate_table': 'wua_irrigationshed',
                'intermediate_field': 'id',
                'intermediate_gis_field': 'name',
            },
            env.ref('wua_maintenance.equipment_category_watermeter').id: {
                'base_table': 'wua_watermeter',
                'base_field': 'irrigationshed_id',
                'gis_table': 'wua_gis_irrigationshed',
                'gis_field': 'name',
                'intermediate_table': 'wua_irrigationshed',
                'intermediate_field': 'id',
                'intermediate_gis_field': 'name',
            },
            env.ref(
                'wua_maintenance.equipment_category_pressuresensor').id: {
                'base_table': 'wua_pressuresensor',
                'base_field': 'name',
                'gis_table': 'wua_gis_pressuresensor',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_irrigationditch').id: {
                'base_table': 'wua_irrigationditch',
                'base_field': 'irrigationditch_code',
                'gis_table': 'wua_gis_irrigationditch',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_drainageditch').id: {
                'base_table': 'wua_drainageditch',
                'base_field': 'drainageditch_code',
                'gis_table': 'wua_gis_drainageditch',
                'gis_field': 'code',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_flowdivider').id: {
                'base_table': 'wua_flowdivider',
                'base_field': 'name',
                'gis_table': 'wua_gis_flowdivider',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_irrigationgate').id: {
                'base_table': 'wua_irrigationgate',
                'base_field': 'name',
                'gis_table': 'wua_gis_irrigationgate',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_airvalve').id: {
                'base_table': 'wua_airvalve',
                'base_field': 'name',
                'gis_table': 'wua_gis_airvalve',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_drainagevalve').id: {
                'base_table': 'wua_drainagevalve',
                'base_field': 'name',
                'gis_table': 'wua_gis_drainagevalve',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_valve').id:  {
                'base_table': 'wua_valve',
                'base_field': 'name',
                'gis_table': 'wua_gis_valve',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_filteringstation').id: {
                'base_table': 'wua_filteringstation',
                'base_field': 'name',
                'gis_table': 'wua_gis_filteringstation',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            env.ref(
                'wua_maintenance.equipment_category_building').id: {
                'base_table': 'wua_building',
                'base_field': 'name',
                'gis_table': 'wua_gis_building',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            self.env.ref(
                'wua_maintenance.equipment_category_processingcentre').id: {
                'base_table': 'wua_processingcentre',
                'base_field': 'name',
                'gis_table': 'wua_gis_processingcentre',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            self.env.ref(
                'wua_maintenance.equipment_category_powerline').id: {
                'base_table': 'wua_powerline',
                'base_field': 'name',
                'gis_table': 'wua_gis_powerline',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
            self.env.ref(
                'wua_maintenance.equipment_category_powerlinesupport').id: {
                'base_table': 'wua_powerlinesupport',
                'base_field': 'name',
                'gis_table': 'wua_gis_powerlinesupport',
                'gis_field': 'name',
                'intermediate_table': False,
                'intermediate_field': False,
                'intermediate_gis_field': False,
            },
        }
        return category_mapping

    @api.model
    def _cron_get_geojson_data(self):
        category_mapping = self._get_category_table_mapping()
        env = self.env
        for category_id, mapping in category_mapping.items():
            base_table = mapping['base_table']
            base_field = mapping['base_field']
            gis_table = mapping['gis_table']
            gis_field = mapping['gis_field']
            intermediate_table = mapping['intermediate_table']
            intermediate_field = mapping['intermediate_field']
            intermediate_gis_field = mapping['intermediate_gis_field']
            if intermediate_table:
                sql = """
                    WITH RECURSIVE category_hierarchy AS (
                        SELECT id FROM maintenance_equipment_category
                        WHERE id = {category_id}
                        UNION ALL
                        SELECT c.id
                        FROM maintenance_equipment_category c
                        JOIN category_hierarchy ch ON c.parent_id = ch.id
                    ),
                    equipment_with_infrastructure_gis AS (
                        SELECT me.id AS equipment_id,
                            ST_AsGeoJSON(gis.geom) AS geojson
                        FROM maintenance_equipment me
                        INNER JOIN {base_table} bt ON me.id = bt.equipment_id
                        INNER JOIN {intermediate_table} it ON bt.{base_field}
                            = it.{intermediate_field}
                        INNER JOIN {gis_table} gis ON
                            it.{intermediate_gis_field} = gis.{gis_field}
                        WHERE me.category_id IN (
                            SELECT id FROM category_hierarchy)
                    )
                    UPDATE maintenance_equipment me
                    SET geojson_geom = eg.geojson, with_infrastructure_gis =
                        TRUE
                    FROM equipment_with_infrastructure_gis eg
                    WHERE me.id = eg.equipment_id
                """.format(
                    base_table=base_table,
                    base_field=base_field,
                    gis_table=gis_table,
                    gis_field=gis_field,
                    intermediate_table=intermediate_table,
                    intermediate_field=intermediate_field,
                    intermediate_gis_field=intermediate_gis_field,
                    category_id=category_id,
                )
            else:
                sql = """
                    WITH RECURSIVE category_hierarchy AS (
                        SELECT id FROM maintenance_equipment_category
                        WHERE id = {category_id}
                        UNION ALL
                        SELECT c.id
                        FROM maintenance_equipment_category c
                        JOIN category_hierarchy ch ON c.parent_id = ch.id
                    ),
                    equipment_with_infrastructure_gis AS (
                        SELECT me.id AS equipment_id, ST_AsGeoJSON(gis.geom)
                            AS geojson
                        FROM maintenance_equipment me
                        INNER JOIN {base_table} bt ON me.id = bt.equipment_id
                        INNER JOIN {gis_table} gis ON bt.{base_field} =
                            gis.{gis_field}
                        WHERE me.category_id IN (
                            SELECT id FROM category_hierarchy)
                    )
                    UPDATE maintenance_equipment me
                    SET geojson_geom = eg.geojson, with_infrastructure_gis =
                        TRUE
                    FROM equipment_with_infrastructure_gis eg
                    WHERE me.id = eg.equipment_id
                """.format(
                    base_table=base_table,
                    base_field=base_field,
                    gis_table=gis_table,
                    gis_field=gis_field,
                    category_id=category_id,
                )
            env.cr.execute(sql)
        cleanup_sql = """
            UPDATE maintenance_equipment
            SET geojson_geom = NULL, with_infrastructure_gis = FALSE
            WHERE geojson_geom IS NULL OR geojson_geom = ''
        """
        env.cr.execute(cleanup_sql)
        # Categories not WUA inherit can inherit from parents
        inherit_geojson_sql = """
        WITH RECURSIVE geo_inheritance AS (
            SELECT id, parent_id, geojson_geom, with_infrastructure_gis
            FROM maintenance_equipment
            WHERE geojson_geom IS NOT NULL AND geojson_geom <> ''
            UNION ALL
            SELECT child.id, child.parent_id, parent.geojson_geom,
                   parent.with_infrastructure_gis
            FROM maintenance_equipment child
            JOIN geo_inheritance parent ON child.parent_id = parent.id
            WHERE child.geojson_geom IS NULL OR child.geojson_geom = ''
        )
        UPDATE maintenance_equipment me
        SET geojson_geom = g.geojson_geom,
            with_infrastructure_gis = g.with_infrastructure_gis
        FROM geo_inheritance g
        WHERE me.id = g.id
        """
        env.cr.execute(inherit_geojson_sql)

    @api.model
    def _cron_generate_requests_with_limit(self):
        for plan in self.env['maintenance.plan'].search([('period', '>', 0)]):
            next_date = fields.Date.from_string(plan.next_creation_date)
            today = fields.Date.from_string(fields.Date.today())
            if next_date <= today:
                equipment = plan.equipment_id
                next_requests = self.env['maintenance.request'].search(
                    [('stage_id.done', '=', False),
                     ('equipment_id', '=', equipment.id),
                     ('maintenance_type', '=', 'preventive'),
                     ('maintenance_kind_id', '=', plan.maintenance_kind_id.id),
                     ('request_date', '=', plan.next_maintenance_date)])
                if not next_requests:
                    equipment._create_new_request(plan)
                    plan.next_creation_date = fields.Date.to_string(
                        fields.Date.from_string(plan.next_creation_date) +
                        timedelta(days=plan.period))

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
            'filteringstation_id',
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

    def _compute_processingcentre_id(self):
        for record in self:
            processingcentre_id = None
            if record.processingcentre_ids:
                processingcentre_id = record.processingcentre_ids[0]
            record.processingcentre_id = processingcentre_id

    def _compute_powerline_id(self):
        for record in self:
            powerline_id = None
            if record.powerline_ids:
                powerline_id = record.powerline_ids[0]
            record.powerline_id = powerline_id

    def _compute_powerlinesupport_id(self):
        for record in self:
            powerlinesupport_id = None
            if record.powerlinesupport_ids:
                powerlinesupport_id = record.powerlinesupport_ids[0]
            record.powerlinesupport_id = powerlinesupport_id

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

    def _compute_building_id(self):
        for record in self:
            building_id = None
            if record.building_ids:
                building_id = record.building_ids[0]
            record.building_id = building_id

    @api.depends('tag_ids')
    def _compute_tag_html(self):
        for record in self:
            tags = None
            if record.tag_ids:
                tags = record.tag_ids.mapped('name')
                tags = ', '.join(tags)
            record.tag_html = tags

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
            self.env.ref('wua_maintenance.equipment_category_intake').id:
                ('wua.intake', _('Intake')),
            self.env.ref('wua_maintenance.equipment_category_reservoir').id:
                ('wua.reservoir', _('Reservoir')),
            self.env.ref('wua_maintenance.equipment_category_pumpgroup').id:
                ('wua.pumpgroup', _('Pumpgroup')),
            self.env.ref(
                'wua_maintenance.equipment_category_photovoltaicplant').id:
                ('wua.photovoltaicplant', _('Photovoltaic Plant')),
            self.env.ref('wua_maintenance.equipment_category_flowmeter').id:
                ('wua.flowmeter', _('Flowmeter')),
            self.env.ref('wua_maintenance.equipment_category_pump').id:
                ('wua.pumpunit', _('Pump')),
            self.env.ref('wua_maintenance.equipment_category_waterpipe').id:
                ('wua.waterpipe', _('Waterpipe')),
            self.env.ref(
                'wua_maintenance.equipment_category_irrigationshed').id:
                ('wua.irrigationshed', _('Irrigationshed')),
            self.env.ref(
                'wua_maintenance.equipment_category_waterconnection').id:
                ('wua.waterconnection', _('Waterconnection')),
            self.env.ref('wua_maintenance.equipment_category_watermeter').id:
                ('wua.watermeter', _('Watermeter')),
            self.env.ref(
                'wua_maintenance.equipment_category_pressuresensor').id:
                ('wua.pressuresensor', _('Pressuresensor')),
            self.env.ref(
                'wua_maintenance.equipment_category_irrigationditch').id:
                ('wua.irrigationditch', _('Irrigation Ditch')),
            self.env.ref(
                'wua_maintenance.equipment_category_drainageditch').id:
                ('wua.drainageditch', _('Drainage Ditch')),
            self.env.ref(
                'wua_maintenance.equipment_category_flowdivider').id:
                ('wua.flowdivider', _('Flowdivider')),
            self.env.ref(
                'wua_maintenance.equipment_category_irrigationgate').id:
                ('wua.irrigationgate', _('Irrigation Gate')),
            self.env.ref(
                'wua_maintenance.equipment_category_airvalve').id:
                ('wua.airvalve', _('Airvalve')),
            self.env.ref(
                'wua_maintenance.equipment_category_drainagevalve').id:
                ('wua.drainagevalve', _('Drainage Valve')),
            self.env.ref(
                'wua_maintenance.equipment_category_valve').id:
                ('wua.valve', _('Valve')),
            self.env.ref(
                'wua_maintenance.equipment_category_filteringstation').id:
                ('wua.filteringstation', _('Filtering Station')),
            self.env.ref(
                'wua_maintenance.equipment_category_building').id:
                ('wua.building', _('Building')),
            self.env.ref(
                'wua_maintenance.equipment_category_processingcentre').id:
                ('wua.processingcentre', _('Processing Centre')),
            self.env.ref(
                'wua_maintenance.equipment_category_powerline').id:
                ('wua.powerline', _('Power Line')),
            self.env.ref(
                'wua_maintenance.equipment_category_powerlinesupport').id:
                ('wua.powerlinesupport', _('Power Line Support')),
        }
        res_model, name = category_mapping.get(
            current_equipment.category_id.id, (None, None))
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

    @api.multi
    def action_get_equipment_childs(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Child Equipments'),
            'res_model': 'maintenance.equipment',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
            'context': {'create': False},
        }
        return act_window

    @api.multi
    def action_see_gis_viewer(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        if (url and self.geojson_geom):
            cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                username, password)
            if (cipher_text):
                url = '%s?arg=%s&geom=%s' % (
                    url, cipher_text, self.geojson_geom)
            else:
                url = '%s?&geom=%s' % (
                    url, self.geojson_geom)
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
