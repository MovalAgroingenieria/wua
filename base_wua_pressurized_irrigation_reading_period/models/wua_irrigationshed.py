# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'

    number_of_waterconnections_reading_mode = fields.Integer(
        string='Number of water connections (Reading Mode)',
        store=True,
        compute='_compute_number_of_waterconnections_reading_mode',
        help='Number of water connections visible in reading mode.')

    @api.depends('waterconnection_ids',
                 'waterconnection_ids.visible_in_reading_mode')
    def _compute_number_of_waterconnections_reading_mode(self):
        for record in self:
            count = 0
            for wc in record.waterconnection_ids:
                if wc.visible_in_reading_mode:
                    count += 1
            record.number_of_waterconnections_reading_mode = count
