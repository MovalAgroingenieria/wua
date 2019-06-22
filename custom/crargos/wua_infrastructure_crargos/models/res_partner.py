# -*- coding: utf-8 -*-).
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    parcel_agent_ids = fields.One2many(
        string='Parcels represented',
        comodel_name='wua.parcel',
        inverse_name='agent_id')

    is_agent = fields.Boolean(
        string='Is agent',
        store=True,
        compute='_compute_is_agent')

    @api.depends('parcel_agent_ids')
    def _compute_is_agent(self):
        for record in self:
            if record.parcel_agent_ids:
                record.is_agent = True
            else:
                record.is_agent = False
