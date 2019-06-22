# -*- coding: utf-8 -*-).
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'

    agent_id = fields.Many2one(
        string='Agent',
        comodel_name='res.partner',
        required=False,
        index=True)

    with_agent = fields.Boolean(
        string="With agent",
        store=True,
        compute='_compute_with_agent')

    @api.depends('agent_id')
    def _compute_with_agent(self):
        for record in self:
            if record.agent_id:
                record.with_agent = True
            else:
                record.with_agent = False
