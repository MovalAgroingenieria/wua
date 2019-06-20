# -*- coding: utf-8 -*-).
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'
    
    agent_id = fields.Many2one(
    string='Agent',
    required=False,
    index=True)
        
    with_agent = fields.Boolean(
    string="With Agent",
    store=True,
    compute='_calculate_with_agent')
    
    @api.multi
    @api.depends('agent_id')
    def _calculate_with_agent(self):
        for record in self:
            if(record.agent_id == None):
                record.with_agent = False
            else:
                record.with_agent = True
