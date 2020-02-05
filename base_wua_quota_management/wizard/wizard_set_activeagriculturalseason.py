# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardSetActiveagriculturalseason(models.TransientModel):
    _name = 'wizard.set.activeagriculturalseason'
    _description = 'Dialog box to choose the active agricultural season'

    agriculturalseason_id = fields.Many2one(
        string='Active Agricultural Season',
        required=True,
        comodel_name='wua.agriculturalseason')

    @api.model
    def default_get(self, var_fields):
        default_agriculturalseason_id = None
        filtered_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if filtered_agriculturalseasons:
            default_agriculturalseason_id = filtered_agriculturalseasons[0].id
        return {'agriculturalseason_id': default_agriculturalseason_id}

    @api.multi
    def set_active_agriculturalseason(self):
        self.ensure_one()
        current_active_agriculturalseason_id = 0
        dict_current_active_agriculturalseason = self.default_get(None)
        if dict_current_active_agriculturalseason['agriculturalseason_id']:
            current_active_agriculturalseason_id = \
                dict_current_active_agriculturalseason['agriculturalseason_id']
        if (self.agriculturalseason_id.id !=
           current_active_agriculturalseason_id):
            if current_active_agriculturalseason_id:
                current_active_agriculturalseason = \
                    self.env['wua.agriculturalseason'].browse(
                        current_active_agriculturalseason_id)
                current_active_agriculturalseason.active_agriculturalseason = \
                    False
            new_active_agriculturalseason = \
                self.env['wua.agriculturalseason'].browse(
                    self.agriculturalseason_id.id)
            new_active_agriculturalseason.active_agriculturalseason = True
            if self.env.context.get('refresh_view', False):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload'
                }
