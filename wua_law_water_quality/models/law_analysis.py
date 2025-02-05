# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class LawAnalysis(models.Model):
    _inherit = 'law.analysis'

    intake_id = fields.Many2one(
        comodel_name='wua.intake',
        index=True,
        ondelete='restrict',
        string='Intake',
    )

    @api.onchange('analysis_template_id')
    def _onchange_analysis_template_id(self):
        super(LawAnalysis, self)._onchange_analysis_template_id()
        self.intake_id = self.analysis_template_id.intake_id
