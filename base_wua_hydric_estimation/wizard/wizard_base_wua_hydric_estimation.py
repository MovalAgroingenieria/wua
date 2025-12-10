# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardBaseWuaHydricEstimation(models.TransientModel):
    _name = 'wizard.base.wua.hydric.estimation'
    _inherit = 'res.config.installer'

    @api.multi
    def execute(self):
        res = super(WizardBaseWuaHydricEstimation, self).execute()
        self.create_cropunits_from_sigpac_enclosures()
        return res

    @api.multi
    def execute_for_parcels(self):
        self.create_cropunits_from_parcels()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def skip_cropunits(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def create_cropunits_from_sigpac_enclosures(self):
        active_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)], limit=1)
        if active_season:
            active_season.generate_weekly_periods()
            active_season.generate_cropunits_from_sigpac_enclosures()

    @api.model
    def create_cropunits_from_parcels(self):
        active_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)], limit=1)
        if active_season:
            active_season.generate_weekly_periods()
            active_season.generate_cropunits_from_parcels()
