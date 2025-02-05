# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class LawAnalysisTemplate(models.Model):
    _inherit = 'law.analysis.template'

    intake_id = fields.Many2one(
        comodel_name='wua.intake',
        index=True,
        ondelete='restrict',
        string='Intake',
    )
