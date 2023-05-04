# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_rest_associated = fields.Selection(
        selection_add=[('inelcom', 'INELCOM')],)

    inelcom_flowmeter_type = fields.Selection(
        [('01_hydrant', 'Hydrant'),
         ('02_head', 'Irrigation Head')],
        string='Inelcom type',
        default='01_hydrant',
    )

    inelcom_irrigation_head_id = fields.Integer(
        string='Irrigation Head ID',
        default='0',
    )

    inelcom_irrigation_head_location = fields.Char(
        string='Location inside Head',
        size=254,
    )

    inelcom_flow_magnitude = fields.Char(
        string='Flow magnitude',
        size=254,
    )

    inelcom_cumulative_reading_magnitude = fields.Char(
        string='Cumulative reading magnitude',
        size=254,
    )

    inelcom_id = fields.Char(
        string='Inelcom code',
        size=254,)
