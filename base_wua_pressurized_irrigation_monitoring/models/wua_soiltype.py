# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaSoiltype(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.soiltype'

    MAX_SIZE_NAME = 40

    name = fields.Char(
        string='Soil Type',
        size=MAX_SIZE_NAME,
        required=True,
        index=True,
        translate=True,
    )

    notes = fields.Html(
        string='Notes'
    )

    subparcel_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.parcel.subparcel',
        inverse_name='soiltype_id',
        readonly=True,
    )

    number_of_subparcels = fields.Integer(
        string='N. of subparcels',
        compute='_compute_number_of_subparcels',
    )

    _sql_constraints = [

    ]

    @api.multi
    def _compute_number_of_subparcels(self):
        for record in self:
            number_of_subparcels = 0
            if (record.subparcel_ids):
                number_of_subparcels = len(record.subparcel_ids)
            record.number_of_subparcels = number_of_subparcels

    @api.multi
    def action_see_subparcels(self):
        self.ensure_one()
        condition = [('soiltype_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_monitoring_parcel_subparcel_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_monitoring_parcel_subparcel_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_monitoring_parcel_subparcel_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Subparcels'),
            'res_model': 'wua.parcel.subparcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.model
    def create(self, vals):
        if 'description' not in vals:
            vals['description'] = ''
        return super(WuaSoiltype, self).create(vals)
