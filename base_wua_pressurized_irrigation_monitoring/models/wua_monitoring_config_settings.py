# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaMonitoringConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.monitoring.configuration'
    _description = 'Configuration of base_wua_pressurized_irrigation_' + \
        'monitoring module'

    max_deviation_categ_01 = fields.Float(
        string='Maximun deviation for Categorie 1',
        default=False,
        help='Maximun percentage of deviation for being in the categorie 01')

    max_deviation_categ_02 = fields.Float(
        string='Maximun deviation for Categorie 2',
        default=False,
        help='Maximun percentage of deviation for being in the categorie 02')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.monitoring.configuration',
                           'max_deviation_categ_01',
                           self.max_deviation_categ_01)
        values.set_default('wua.monitoring.configuration',
                           'max_deviation_categ_02',
                           self.max_deviation_categ_02)
