# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaPressuresensor(models.Model):
    _inherit = 'wua.pressuresensor'

    telecontrol_associated = fields.Selection(
        selection_add=[('inelcom', 'INELCOM')],)

    inelcom_pressuresensor_type = fields.Selection(
        [('01_hydrant', 'Hydrant'),
         ('02_head', 'Irrigation Head')],
        string='Inelcom type',
        default='01_hydrant',
    )

    inelcom_hydrant_analog = fields.Selection(
        [('01_analog', 'Analog Measurement 1'),
         ('02_analog', 'Analog Measurement 2')],
        string='Analog Measurement',
        default='01_analog',
    )

    inelcom_irrigation_head_id = fields.Integer(
        string='Irrigation Head ID',
        default='0',
    )

    inelcom_id = fields.Char(
        string='Inelcom code',
        size=254,
    )
