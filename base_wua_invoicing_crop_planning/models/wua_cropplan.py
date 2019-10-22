# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaEnrolledsubparcel(models.Model):
    _inherit = 'wua.enrolledsubparcel'

    contracted_volume = fields.Float(
        string='Contracted Water (m3)',
        store=True,
        index=True,
        compute='_compute_contracted_volume'
    )

    @api.depends('area_official', 'agriculturalseason_id.volume_perunitarea')
    def _compute_contracted_volume(self):
        for record in self:
            contracted_volume = 0
            if (record.agriculturalseason_id.volume_perunitarea):
                contracted_volume = record.area_official * \
                    record.agriculturalseason_id.volume_perunitarea
            record.contracted_volume = contracted_volume
