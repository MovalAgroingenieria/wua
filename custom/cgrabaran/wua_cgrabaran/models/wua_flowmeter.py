# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    scada_remote_code = fields.Char(
        string='Scada Remote Code',
        index=True,
        size=20)

    scada_identifier = fields.Char(
        string='Scada ID',
        index=True,
        size=20)

    scada_info_type = fields.Char(
        string='Scada Info Type',
        index=True,
        size=20)

    sql_constraints = [
        ('unique_scada_info',
         'UNIQUE (scada_remote_code, scada_identifier, scada_info_type)',
         'Existing combination of scada id\'s.'),
        ]
