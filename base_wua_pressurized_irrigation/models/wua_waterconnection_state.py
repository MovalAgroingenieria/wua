# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json
from lxml import etree
from odoo import models, fields, api, tools, _


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
        if self.filtered(lambda x: x.default_state):
            if len(self) > 1:
                raise models.ValidationError(
                    _('Only one state can be set as default.'))
            if not self.active:
                raise models.ValidationError(
                    _('The default state must be active.'))
    