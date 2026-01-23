# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardCropunitCreationSummary(models.TransientModel):
    _name = 'wizard.cropunit.creation.summary'
    _description = 'Crop Unit Creation Summary'

    message = fields.Text(
        string='Summary',
        readonly=True,
    )

    @api.multi
    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
