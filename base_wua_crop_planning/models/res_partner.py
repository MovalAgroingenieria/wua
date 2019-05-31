# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False,
        store=True,
        compute='_compute_registered_cropplan')

    @api.depends('cropplan_id')
    def _compute_registered_cropplan(self):
        for record in self:
            registered_cropplan = False
            if record.cropplan_id:
                registered_cropplan = True
            record.registered_cropplan = registered_cropplan
