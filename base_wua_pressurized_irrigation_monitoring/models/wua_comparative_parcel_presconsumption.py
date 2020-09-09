# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, tools


class WuaComparativeParcelPresconsumption(models.Model):
    _name = 'wua.comparative.parcel.presconsumption'
    _description = 'Comparative Parcel Presconsumption'
    _auto = False
    _order = 'controlperiod_id'

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
        index=True,
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4)
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4)
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4)
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4)
    )

    cadastral_reference_link = fields.Char(
        string='Cadastral Report'
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer'
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_comparative_parcel_presconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_comparative_parcel_presconsumption AS (
            SELECT row_number() OVER () AS id, wcsp1.controlperiod_id,
            wcsp1.parcel_id, SUM(wcsp1.estimated_consumption) AS
            estimated_consumption, SUM(wcsp1.real_consumption) AS
            real_consumption, SUM(wcsp1.deviation) AS deviation,
            wcsp1.agriculturalseason_id, wcsp1.hydraulicsector_id,
            wcsp1.partner_id, wp1.area_official, wcsp1.gis_viewer_link,
            wcsp1.cadastral_reference_link FROM
            wua_comparative_subparcel_presconsumption wcsp1 INNER JOIN
            wua_parcel wp1 ON wp1.id = wcsp1.parcel_id GROUP BY
            wcsp1.parcel_id, wcsp1.controlperiod_id,
            wcsp1.agriculturalseason_id, wcsp1.hydraulicsector_id,
            wcsp1.partner_id, wp1.area_official, wcsp1.gis_viewer_link,
            wcsp1.cadastral_reference_link)
            """)
