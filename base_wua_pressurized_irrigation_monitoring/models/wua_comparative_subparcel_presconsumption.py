# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaComparativeSubparcelPresconsumption(models.Model):
    _name = 'wua.comparative.subparcel.presconsumption'
    _description = 'Comparative Subparcel Presconsumption'

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
    )

    subparcel_id = fields.Many2one(
        string='Subparcel',
        comodel_name='wua.parcel.subparcel',
        index=True,
        ondelete='restrict',
    )

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
        index=True,
        ondelete='cascade',
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id'
    )

    theoretical_consumption = fields.Float(
        string='Theoretical Consumption',
        digits=(32, 4),
        default=0,
        compute='_compute_theoretical_consumption',
        store=True
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4),
        default=0
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4),
        default=0
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True,
    )

    regularization = fields.Float(
        string='Regularization',
        digits=(32, 4),
        default=0
    )

    notes = fields.Html(
        string='Notes'
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict'
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict'
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        ondelete='restrict'
    )

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        ondelete='restrict'
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0
    )

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        ondelete='restrict'
    )

    shaded_percentage = fields.Float(
        string='Shaded Percentage',
        digits=(32, 2)
    )

    soil_type = fields.Selection([
        ('loamy', 'Loamy'),
        ('clayey', 'Clayey'),
        ('silty', 'Silty'),
        ('sandy', 'Sandy'),
        ('loam_clayey', 'Loam-Clayey'),
        ('loam_silty', 'Loam-Silty'),
        ('loam_sandy', 'Loam-Sandy'),
        ],
        string='Soil Type'
    )

    organic_material_percentage = fields.Float(
        string='Organica Material Percentage',
        digits=(32, 2)
    )

    orientation = fields.Integer(
        string='Orientation',
        help='Value between 0 and 359º (0 corresponds to geographic north)'
    )

    drippers_number = fields.Integer(
        string='Number of Drippers'
    )

    drippers_nomial_flow = fields.Float(
        string='Drippers Nomial Flow (l/h)',
        digits=(32, 2)
    )

    plantation_year = fields.Integer(
        string='Plantation Year'
    )

    cultivation_age = fields.Integer(
        string='Cultivation Age'
    )

    cadastral_reference = fields.Char(
        string='Cadastral Reference'
    )

    cadastral_reference_link = fields.Char(
        string='Cadastral Report',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
    )

    updated_in_remotecontrol = fields.Boolean(
        string='Updated in Remote Control',
    )

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
    )

    tree_distance = fields.Float(
        string='Distance between trees (m)',
        digits=(32, 2),
    )

    tree_drippers_number = fields.Integer(
        string='Number of drippers by tree',
    )

    tree_development = fields.Selection([
        ('seedlings', 'Seedlings'),
        ('intermediate', 'Intermediate'),
        ('full_production', 'Full production')],
        string='Tree Development',
    )

    tree_lateral_number = fields.Integer(
        string='Number of tree laterals ',
    )

    row_distance = fields.Float(
        string='Distance between rows (m)',
        digits=(32, 2),
    )

    area_perc = fields.Float(
        string='%',
        digits=(5, 2),
    )

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.depends('regularization')
    def _compute_theoretical_consumption(self):
        for record in self:
            theoretical_consumption = record.regularization
            record.theoretical_consumption += theoretical_consumption

    @api.depends('controlperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if (record.controlperiod_id):
                agriculturalseason_id = \
                    record.controlperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.model
    def create(self, vals):
        cmp_pres = super(WuaComparativeSubparcelPresconsumption, self).\
            create(vals)
        if (cmp_pres.controlperiod_id.controlpresconsumption_ids):
            for ctrl_pres in \
                    cmp_pres.controlperiod_id.controlpresconsumption_ids:
                total_area = ctrl_pres.waterconnection_id.\
                    total_affected_area_official
                for ip in ctrl_pres.waterconnection_id.irrigationpoint_ids:
                    if (cmp_pres.subparcel_id in ip.parcel_id.subparcel_ids):
                        prorrated = ctrl_pres.volume_real * \
                            ((cmp_pres.subparcel_id.area_official)/total_area)
                        cmp_pres.real_consumption += prorrated
        return cmp_pres
