# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def get_agriculturalseason_id(self):
        for record in self:
            quota = self.env['wua.quota'].search([
                ('partner_id.id', '=', record.id),
                ('agriculturalseason_id.active_agriculturalseason',
                 '=', 'true')], limit=1)
            agriculturalseason_id = None
            if quota:
                agriculturalseason_id = quota[0].agriculturalseason_id
        return agriculturalseason_id

    @api.multi
    def get_partner_active_agriculturalseason_quotas(self, quotaperiod_id):
        for record in self:
            quotas = self.env['wua.quota'].search([
                ('partner_id.id', '=', record.id),
                ('agriculturalseason_id.active_agriculturalseason', '=',
                 'true'), ('quotaperiod_id', '=', quotaperiod_id)])
        return quotas

    @api.multi
    def get_partner_active_agriculturalseason_hydricmovements(self):
        for record in self:
            hydricmovements = self.env['wua.hydricmovement'].search([
                ('partner_id.id', '=', record.id),
                ('agriculturalseason_id.active_agriculturalseason',
                 '=', 'true')], order="event_time asc")
        return hydricmovements

    def get_quotaperiod_of_agriculturalseason(self, agriculturalseason_id):
        quotaperiods = self.env['wua.quotaperiod'].search(
            [('agriculturalseason_id', '=', agriculturalseason_id)],
            order="initial_date asc")
        return quotaperiods
