# -*- coding: utf-8 -*-).
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    share = fields.Integer(
        string='Share',
        default=0,
        index=True)

    _sql_constraints = [
        ('valid_share',
         'CHECK (share >= 0)',
         'The number of shares must be a value zero or positive.'),
        ]
