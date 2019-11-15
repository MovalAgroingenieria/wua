# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaInFm(models.Model):
    _name = 'wua.in.fm'
    _description = 'Entity (intake/flowmeter)'

    intake_id = fields.Many2one(
        string='Intake',
        required=True,
        comodel_name='wua.flowmeter',
        ondelete='cascade')

    flowmeter_id = fields.Many2one(
        string='Flowmeter',
        required=True,
        comodel_name='wua.flowmeter',
        ondelete='cascade')

    assing_start = fields.Date(
        string='From date',
        required=True,
        default=lambda self: fields.datetime.now())
