# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaCropplan(models.Model):
    _inherit = 'wua.cropplan'

    current_balance = fields.Float(
        strin="Current balance (m3)",
        digits=(32, 2),
        store=False,
        compute='_compute_current_balance')

    def _get_hydricmovements(self, partner_id):
        hydric_movements = False
        hydric_movements = self.env['wua.hydricmovement'].search([
            ('partner_id', '=', partner_id.id),
            ('of_active_agriculturalseason', '=', True)], order='name')
        return hydric_movements

    @api.multi
    def _compute_current_balance(self):
        for record in self:
            balance = 0.0
            hydric_movs = record.env['wua.hydricmovement'].search([
                ('partner_id', '=', record.partner_id.id),
                ('of_active_agriculturalseason', '=', True)])
            for hydric_mov in hydric_movs:
                balance += hydric_mov.accounting_volume
            record.current_balance = balance
