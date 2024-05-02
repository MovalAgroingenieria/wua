# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    octroi_id = fields.Many2one(
        string='Octroi',
        comodel_name='wua.octroi',
        index=True,
        ondelete='restrict',
    )

    waterchannel_id = fields.Many2one(
        string='Waterchannel',
        comodel_name='wua.waterchannel',
        index=True,
        ondelete='restrict',
    )
