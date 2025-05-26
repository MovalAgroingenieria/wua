# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api, exceptions, _


class MaintenanceStage(models.Model):
    _inherit = "maintenance.stage"

    requests_visible_on_gis = fields.Boolean(
        string='Requests visible on GIS',
        default=False,
    )

    default_stage_for_viewer_creation = fields.Boolean(
        string='Default stage for viewer creation',
        default=False,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.constrains('default_stage_for_viewer_creation')
    def _check_default_stage_for_viewer_creation(self):
        for record in self:
            if record.default_stage_for_viewer_creation:
                if self.search_count([
                    ('default_stage_for_viewer_creation', '=', True),
                ]) > 1:
                    raise exceptions.ValidationError(_(
                        'Only one stage can be the default stage '
                        'for viewer creation',
                    ))
