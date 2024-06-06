# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class LawAnalysis(models.Model):
    _inherit = 'law.analysis'

    intake_id = fields.Many2one(
        comodel_name='wua.intake',
        index=True,
        ondelete='restrict',
        string='Intake',
    )
