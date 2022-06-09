# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _


class WuaZone(models.Model):
    _name = 'wua.zone'
    _description = 'Zone'
    _order = 'zone_code'

    # Size of field "name".
    MAX_SIZE_NAME = 75

    def _default_zone_code(self):
        resp = 0
        zones = self.search([], limit=1,
                            order='zone_code desc')
        if zones:
            resp = zones[0].zone_code + 1
        else:
            resp = 1
        return resp

    zone_code = fields.Integer(
        string='Code',
        default=_default_zone_code,
        required=True,
        index=True)

    name = fields.Char(
        string='Name',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    notes = fields.Html(
        string='Notes')

    hydraulicsector_ids = fields.One2many(
        comodel_name='wua.hydraulicsector',
        inverse_name='zone_id',
        string='Hydraulic sectors of zone')

    number_of_hydraulicsectors = fields.Integer(
        string='Number of hydraulic sectors',
        compute='_compute_number_of_hydraulicsectors')

    _sql_constraints = [
        ('valid_zone_code', 'CHECK (zone_code > 0)',
         'The code of zone must be a positive value.'),
        ('unique_zone_code', 'UNIQUE (zone_code)',
         'Existing code of zone.'),
        ('unique_name', 'UNIQUE (name)',
         'Existing name.'),
        ]

    @api.multi
    def _compute_number_of_hydraulicsectors(self):
        for record in self:
            number_of_hydraulicsectors = 0
            if record.hydraulicsector_ids:
                number_of_hydraulicsectors = len(record.hydraulicsector_ids)
            record.number_of_hydraulicsectors = number_of_hydraulicsectors

    @api.multi
    def action_get_hydraulicsectors(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_hydraulicsector_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_hydraulicsector_view_form').id
        search_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_hydraulicsector_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Hydraulic Sectors'),
            'res_model': 'wua.hydraulicsector',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.hydraulicsector_ids.ids)],
            'context': {'default_zone_id': self.id}
            }
        return act_window
