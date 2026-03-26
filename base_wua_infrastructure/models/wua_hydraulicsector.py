# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.hydraulicsector'
    _description = 'Entity (hydraulic sector)'
    _order = 'hydraulicsector_code'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    def _default_hydraulicsector_code(self):
        resp = 0
        hydraulicsectors = self.search([('hydraulicsector_code', '>', 0)],
                                       limit=1,
                                       order='hydraulicsector_code desc')
        if len(hydraulicsectors) == 1:
            resp = hydraulicsectors[0].hydraulicsector_code + 1
        else:
            resp = 1
        return resp

    name = fields.Char(string='Hydraulic Sector')

    hydraulicsector_code = fields.Integer(
        string='Code',
        default=_default_hydraulicsector_code,
        required=True,
        index=True)

    notes = fields.Html(string='Notes')

    irrigationshed_ids = fields.One2many(
        string='Irrigation Sheds',
        comodel_name='wua.irrigationshed',
        inverse_name='hydraulicsector_id')

    waterconnection_ids = fields.One2many(
        string='Water Connections',
        comodel_name='wua.waterconnection',
        inverse_name='hydraulicsector_id')

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='hydraulicsector_id')

    number_of_irrigationsheds = fields.Integer(
        string='Number of irrigation sheds',
        store=True,
        compute='_compute_number_of_irrigationsheds')

    number_of_waterconnections = fields.Integer(
        string='Number of water connections',
        store=True,
        compute='_compute_number_of_waterconnections')

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    total_affected_area_official = fields.Float(
        string='Cumulative area of parcels',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official')

    total_affected_area_official_hec = fields.Float(
        string='Cumulative area of parcels (hectares)',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official_hec')

    zone_id = fields.Many2one(
        string='Zone',
        comodel_name='wua.zone',
        index=True,
        ondelete='restrict')

    @api.depends('irrigationshed_ids', 'irrigationshed_ids.active')
    def _compute_number_of_irrigationsheds(self):
        for record in self:
            record.number_of_irrigationsheds = \
                len(record.irrigationshed_ids)

    @api.depends('waterconnection_ids', 'waterconnection_ids.active')
    def _compute_number_of_waterconnections(self):
        for record in self:
            record.number_of_waterconnections = \
                len(record.waterconnection_ids)

    @api.depends('irrigationshed_ids',
                 'irrigationshed_ids.number_of_parcels',
                 'irrigationshed_ids.active')
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = \
                sum(record.mapped('irrigationshed_ids.number_of_parcels'))

    @api.depends('irrigationshed_ids',
                 'irrigationshed_ids.total_affected_area_official',
                 'irrigationshed_ids.active')
    def _compute_total_affected_area_official(self):
        for record in self:
            record.total_affected_area_official = \
                sum(record.mapped(
                    'irrigationshed_ids.total_affected_area_official'))

    @api.depends('total_affected_area_official')
    def _compute_total_affected_area_official_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        for record in self:
            record.total_affected_area_official_hec = \
                factor * record.total_affected_area_official

    @api.constrains('hydraulicsector_code')
    def _check_hydraulicsector_code(self):
        if self.hydraulicsector_code <= 0:
            raise exceptions.ValidationError(_('The hydraulic sector code '
                                               'must be a positive value.'))

    @api.model
    def create(self, vals):
        new_hydraulicsector = super(WuaHydraulicsector, self).create(vals)
        if 'hydraulicsector_code' in vals:
            correct_hydraulicsector_code = \
                not self.exists_hydraulicsector_code(
                    vals['hydraulicsector_code'], new_hydraulicsector.id)
            if not correct_hydraulicsector_code:
                raise exceptions.UserError(_('The hydraulic sector '
                                             'code already exists.'))
        return new_hydraulicsector

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.hydraulicsector_code > 0:
                name = record.name + ' ' + \
                    '[' + str(record.hydraulicsector_code) + ']'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.multi
    def write(self, vals):
        if 'hydraulicsector_code' in vals:
            correct_hydraulicsector_code = \
                not self.exists_hydraulicsector_code(
                    vals['hydraulicsector_code'], self.id)
            if not correct_hydraulicsector_code:
                raise exceptions.UserError(_('The hydraulic sector code '
                                             'already exists.'))
        return super(WuaHydraulicsector, self).write(vals)

    def exists_hydraulicsector_code(self, hydraulicsector_code, excluded_id):
        resp = False
        if hydraulicsector_code > 0:
            hydraulicsectors = self.env['wua.hydraulicsector'].search([])
            for hydraulicsector in hydraulicsectors:
                if (hydraulicsector.hydraulicsector_code ==
                   hydraulicsector_code and
                   excluded_id != hydraulicsector.id):
                    resp = True
                    break
        return resp

    def get_wua_hydraulicsector_parcels_action(self):
        current_hydraulicsector_id = self.env.context.get('active_id')
        current_hydraulicsector = self.browse(current_hydraulicsector_id)
        if current_hydraulicsector:
            parcel_ids = []
            parcel_irrigation_points = self.env['wua.parcel.irrigationpoint']
            for waterconnection in current_hydraulicsector.waterconnection_ids:
                filtered_parcel_irrigation_points = \
                    parcel_irrigation_points.search(
                        [('waterconnection_id', '=', waterconnection.id)])
                for parcel_irrig_point in filtered_parcel_irrigation_points:
                    parcel_ids.append(parcel_irrig_point.parcel_id.id)
            condition = [('id', 'in', parcel_ids)]
            id_tree_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_tree').id
            id_form_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_form').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Parcels'),
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'domain': condition,
                'target': 'current',
                'context': self.env.context,
                }
            return act_window
