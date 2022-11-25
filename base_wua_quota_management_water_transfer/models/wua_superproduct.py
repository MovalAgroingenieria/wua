# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaSuperproduct(models.Model):
    _inherit = 'wua.superproduct'

    is_transferable = fields.Boolean(
        string='Is transferable',
        default=False)

    transfer_superproduct_id = fields.Many2one(
        string='Superproduct to transfer',
        comodel_name='wua.superproduct',
        index=True,
        ondelete='restrict',)
