# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        domain=[('parent_id', '!=', False)],
        ondelete='restrict')

    is_mapped_to_company = fields.Boolean(
        string='Mapped to a company',
        store=True,
        compute='_compute_is_mapped_to_company')

    _sql_constraints = [
        ('unique_company_id', 'UNIQUE (company_id)',
         'Company assigned to another intake.'),
        ]

    @api.depends('company_id')
    def _compute_is_mapped_to_company(self):
        for record in self:
            is_mapped_to_company = False
            if record.company_id:
                is_mapped_to_company = True
            record.is_mapped_to_company = is_mapped_to_company
