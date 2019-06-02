# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        ondelete='set null',
        readonly=True)

    enrolledsubparcel_ids = fields.One2many(
        string='Enrolled Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='partner_id')

    number_of_enrolledsubparcels = fields.Integer(
        string='Number of enrolled subp.',
        compute='_compute_number_of_enrolledsubparcels')

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False,
        store=True,
        compute='_compute_registered_cropplan')

    exists_active_agriculturalseason = fields.Boolean(
        string='Exists a active agricultural season',
        compute='_compute_exists_active_agriculturalseason')

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
