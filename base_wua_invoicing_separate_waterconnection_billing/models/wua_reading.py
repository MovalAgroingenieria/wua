# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    watercosts_partner_id = fields.Many2one(
        string='Partner for water costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_watercosts_partner_id')

    @api.depends('waterconnection_id')
    def _compute_watercosts_partner_id(self):
        for record in self:
            watercosts_partner_id = None
            if record.waterconnection_id.watercosts_partner_id:
                watercosts_partner_id = record.waterconnection_id.\
                    watercosts_partner_id
            record.watercosts_partner_id = watercosts_partner_id
