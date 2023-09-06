# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWaterconnectionIrrigationShift(models.Model):
    _name = 'wua.waterconnection.irrigation.shift'
    _description = 'Entity (waterconnection irrigation shift)'
    _order = 'name ASC'

    MAX_SIZE_NAME = 52

    waterconnection_ids = fields.One2many(
        string='Water Connections',
        comodel_name='wua.waterconnection',
        inverse_name='irrigation_shift_id',
        ondelete='set null',
    )

    name = fields.Char(
        string='Name',
        size=MAX_SIZE_NAME,
        required=True,
        index=True,
    )

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_NAME,
        index=True,
    )
    notes = fields.Html(
        string='Notes',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Irrigation Shift.'),
    ]

    @api.multi
    def action_see_waterconnections(self):
        self.ensure_one()
        condition = [('irrigation_shift_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_tree').id
        search_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_search')
        waterconnections = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
            'base_wua_infrastructure',
            'Waterconnections')
        if (not waterconnections):
            waterconnections = _('Waterconnections')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': waterconnections,
            'res_model': 'wua.waterconnection',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'from_shortcut': 1},
            }
        return act_window
