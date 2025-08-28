# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WizardRecalculateQuoas(models.TransientModel):
    _name = 'wizard.recalculate.quotas'
    _description = 'Dialog box to do a global recalculation of quotas'

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        readonly=True,
        comodel_name='wua.agriculturalseason')

    agriculturalseason_name = fields.Char(
        string='Name of agricultural season',
        readonly=True)

    @api.model
    def default_get(self, var_fields):
        default_agriculturalseason_id = None
        default_agriculturalseason_name = ''
        filtered_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if filtered_agriculturalseasons:
            default_agriculturalseason = filtered_agriculturalseasons[0]
            initial_date_str = self.env['wua.parcel'].\
                transform_date_to_locale(
                    default_agriculturalseason.initial_date)
            end_date_str = self.env['wua.parcel'].\
                transform_date_to_locale(default_agriculturalseason.end_date)
            if default_agriculturalseason.description:
                default_agriculturalseason_name = initial_date_str + ' - ' + \
                    end_date_str + ' ' + \
                    '[' + default_agriculturalseason.description + ']'
            else:
                default_agriculturalseason_name = initial_date_str + ' - ' + \
                    end_date_str
            default_agriculturalseason_id = default_agriculturalseason.id
        return {
            'agriculturalseason_id': default_agriculturalseason_id,
            'agriculturalseason_name': default_agriculturalseason_name,
            }

    @api.multi
    def do_recalculation_quotas(self):
        self.ensure_one()
        if self.agriculturalseason_id:
            self.env['wua.quota'].recalculate_quotas(
                self.agriculturalseason_id)
        if self.env.context.get('refresh_view', False):
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }
