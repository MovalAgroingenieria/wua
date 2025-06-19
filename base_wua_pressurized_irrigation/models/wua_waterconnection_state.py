# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError



class WuaWaterconnectionState(models.Model):
    _name = 'wua.waterconnection.state'

    name = fields.Char(
        string='State',
        required=True,
        translate=True)
    description = fields.Text(
        string='Description',
        translate=True)
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, it will allow you to hide the state without '
             'removing it.')
    default_state = fields.Boolean(
        string='Default State',
        default=False,
        help='If checked, it will set this state as the default for new '
             'water connections.')
    is_close = fields.Boolean(
        string='Is Closed',
        default=False,
        help='If checked, it will allow you to close the water connection '
             'and prevent any further changes to it.')
    notes = fields.Html(
        string='Notes',
        translate=True,
        help='Additional information about the state.')
    waterconnection_ids = fields.One2many(
        string='Water Connections',
        comodel_name='wua.waterconnection',
        inverse_name='watermeter_id',
        help='Water connections that are in this state.')
    
    @api.constrains('default_state')
    def _check_default_state(self):
        for record in self:
            if record.default_state:
                # Verifica si hay otro registro con default_state=True
                others = self.search([
                    ('id', '!=', record.id),
                    ('default_state', '=', True),
                ])
                if others:
                    raise ValidationError(_('Only one state can be set as default.'))
                if not record.active:
                    raise ValidationError(_('The default state must be active.'))
    