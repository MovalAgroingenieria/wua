# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    octroi_id = fields.Many2one(
        string='Octroi',
        comodel_name='wua.octroi',
    )
