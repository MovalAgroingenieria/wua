# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    watercosts_partner_id = fields.Many2one(
        string='Partner for water costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_watercosts_partner_id')

    othercosts_partner_id = fields.Many2one(
        string='Partner for other costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_othercosts_partner_id')

    @api.depends('partnerlink_ids')
    def _compute_watercosts_partner_id(self):
        for record in self:
            watercosts_partner_id = None
            number_of_partnerlinks = 0
            possible_partner_id = None
            for partnerlink in record.partnerlink_ids:
                if partnerlink.water_costs_percentage > 0:
                    possible_partner_id = partnerlink.partner_id
                    number_of_partnerlinks = number_of_partnerlinks + 1
                    if number_of_partnerlinks > 1:
                        break
            if number_of_partnerlinks == 1:
                watercosts_partner_id = possible_partner_id
            record.watercosts_partner_id = watercosts_partner_id

    @api.depends('partnerlink_ids')
    def _compute_othercosts_partner_id(self):
        for record in self:
            othercosts_partner_id = None
            number_of_partnerlinks = 0
            possible_partner_id = None
            for partnerlink in record.partnerlink_ids:
                if partnerlink.other_costs_percentage > 0:
                    possible_partner_id = partnerlink.partner_id
                    number_of_partnerlinks = number_of_partnerlinks + 1
                    if number_of_partnerlinks > 1:
                        break
            if number_of_partnerlinks == 1:
                othercosts_partner_id = possible_partner_id
            record.othercosts_partner_id = othercosts_partner_id
