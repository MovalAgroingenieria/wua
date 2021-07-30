# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    employee_as_secretary_id = fields.Many2one(
        string='Secretary of WUA',
        comodel_name='hr.employee',
        ondelete='restrict')
