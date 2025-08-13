# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, exceptions, api, _


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.team"

    category_id = fields.Many2one(
        string='Maintenance category',
        comodel_name='maintenance.equipment.category',
        store=True,
    )

    partner_ids = fields.Many2many(
        string='Partners',
        comodel_name='res.partner',
    )

    name = fields.Char(
        translate=True,
    )

    active = fields.Boolean(
        default=True,
    )

    default_team_for_viewer_creation = fields.Boolean(
        string='Default team for viewer creation',
        default=False,
    )

    default_team = fields.Boolean(
        string='Default team',
        default=False,
    )

    @api.constrains('default_team_for_viewer_creation')
    def _check_default_team_for_viewer_creation(self):
        for record in self:
            if record.default_team_for_viewer_creation:
                if self.search_count([
                    ('default_team_for_viewer_creation', '=', True),
                ]) > 1:
                    raise exceptions.ValidationError(_(
                        'Only one team can be the default team '
                        'for viewer creation',
                    ))

    @api.constrains('default_team')
    def _check_default_team(self):
        for record in self:
            if record.default_team:
                if self.search_count([
                    ('default_team', '=', True),
                ]) > 1:
                    raise exceptions.ValidationError(_(
                        'Only one team can be the default team ',
                    ))
