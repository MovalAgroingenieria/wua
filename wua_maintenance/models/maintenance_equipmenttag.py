# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _


class MaintenanceEquipmentTag(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'maintenance.equipmenttag'
    _description = 'Maintenance Equipment Tag'

    _size_name = 25
    _size_description = 75
    _numeric_name = False
    _lowercase_name = True
    _uppercase_name = False

    _sql_constraints = [('name_uniq', 'unique (name)',
                         _("Maintenance tag already exists."))]

    name = fields.Char(string='Equipment Tag')

    color = fields.Integer(
        string='Color Index',
        help='0:grey, 1:green, 2:yellow, ' +
        '3:orange, 4:red, 5:purple, 6:blue, ' +
        '7:cyan, 8:light-green, 9:magenta')

    notes = fields.Html(string="Notes")
