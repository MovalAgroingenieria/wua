# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    cropfamily_id = fields.Many2one(
        string='Crop Family',
        comodel_name='wua.cropfamily',
        index=True,
    )

    suitable_hydric_estimation = fields.Boolean(
        string='Suitable for hydric estimation',
        default=True,
        required=True,
    )

    kc_a = fields.Float(
        string='Coefficient a in the quadratic function of Kc',
        digits=(32, 4),
        compute='_compute_kc_a',
    )

    kc_b = fields.Float(
        string='Coefficient b in the quadratic function of Kc',
        digits=(32, 4),
        compute='_compute_kc_b',
    )

    kc_c = fields.Float(
        string='Coefficient c in the quadratic function of Kc',
        digits=(32, 4),
        compute='_compute_kc_c',
    )

    @api.multi
    def _compute_kc_a(self):
        for record in self:
            kc_a = 0
            if record.suitable_hydric_estimation and record.cropfamily_id:
                kc_a = record.cropfamily_id.kc_a
            record.kc_a = kc_a

    @api.multi
    def _compute_kc_b(self):
        for record in self:
            kc_b = 0
            if record.suitable_hydric_estimation and record.cropfamily_id:
                kc_b = record.cropfamily_id.kc_b
            record.kc_b = kc_b

    @api.multi
    def _compute_kc_c(self):
        for record in self:
            kc_c = 0
            if record.suitable_hydric_estimation and record.cropfamily_id:
                kc_c = record.cropfamily_id.kc_c
            record.kc_c = kc_c
