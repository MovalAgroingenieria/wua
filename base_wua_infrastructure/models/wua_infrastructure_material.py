# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaInfrastructureMaterial(models.Model):
    _name = 'wua.infrastructure.material'
    _description = 'Infrastructure Material'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Infrastructure Material',
    )

    notes = fields.Html(
        string="Notes",
    )
