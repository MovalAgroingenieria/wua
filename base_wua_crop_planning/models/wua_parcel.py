# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        ondelete='set null',
        readonly=True)

    enrolledsubparcel_ids = fields.One2many(
        string='Enrolled Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='parcel_id')

    number_of_enrolledsubparcels = fields.Integer(
        string='Number of enrolled subp.',
        compute='_compute_number_of_enrolledsubparcels')

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False,
        store=True,
        compute='_compute_registered_cropplan')

    can_be_watered = fields.Boolean(
        string='Can be watered',
        default=True,
        store=True,
        compute='_compute_can_be_watered')

    exists_active_agriculturalseason = fields.Boolean(
        string='Exists a active agricultural season',
        compute='_compute_exists_active_agriculturalseason')

    permanent = fields.Boolean(
        string='Permanent',
        default=False)

    with_second_cultivation = fields.Boolean(
        string="With Second Cultivation",
        compute='_compute_with_second_cultivation',
        store=True
    )

    @api.depends('cropplan_id', 'cropplan_id.with_second_cultivation')
    def _compute_with_second_cultivation(self):
        for record in self:
            with_second_cultivation = False
            if record.cropplan_id and \
                    record.cropplan_id.with_second_cultivation:
                with_second_cultivation = True
            record.with_second_cultivation = with_second_cultivation

    @api.multi
    def _compute_number_of_enrolledsubparcels(self):
        for record in self:
            number_of_enrolledsubparcels = 0
            if record.enrolledsubparcel_ids:
                number_of_enrolledsubparcels = \
                    len(record.enrolledsubparcel_ids)
            record.number_of_enrolledsubparcels = number_of_enrolledsubparcels

    @api.depends('cropplan_id')
    def _compute_registered_cropplan(self):
        for record in self:
            registered_cropplan = False
            if record.cropplan_id:
                registered_cropplan = True
            record.registered_cropplan = registered_cropplan

    @api.multi
    def _compute_exists_active_agriculturalseason(self):
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        exists_active_agriculturalseason = False
        if active_agriculturalseasons:
            exists_active_agriculturalseason = True
        for record in self:
            record.exists_active_agriculturalseason = \
                exists_active_agriculturalseason

    @api.depends('registered_cropplan',
                 'subparcel_ids',
                 'subparcel_ids.is_cultivable')
    def _compute_can_be_watered(self):
        for record in self:
            can_be_watered = False
            if record.registered_cropplan:
                cultivable_subparcels = \
                    record.subparcel_ids.filtered(lambda x: x.is_cultivable)
                if cultivable_subparcels:
                    can_be_watered = True
            record.can_be_watered = can_be_watered

    @api.multi
    def name_get(self):
        result = []
        if self.env.context.get('in_combo', False):
            for record in self:
                parcel_code = record.name
                area_official_str = _('area:') + ' ' + \
                    '{:.4f}'.format(record.area_official)
                result.append((record.id, parcel_code + ' (' +
                               area_official_str + ')'))
        else:
            for record in self:
                result.append((record.id, record.name))
        return result

    @api.multi
    def action_see_enrolledsubparcels(self):
        self.ensure_one()
        if self.enrolledsubparcel_ids:
            id_tree_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_form').id
            search_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Enrolled Subparcels'),
                'res_model': 'wua.enrolledsubparcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.enrolledsubparcel_ids.ids)],
                'context': {'search_default_active_agriculturalseason': 1,
                            'reduced_name_get_for_agriculturalseason': True,
                            'reduced_name_get_for_cropplan': True}
                }
            return act_window
