# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaMaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    name = fields.Char('Name', required=True, translate=True)

    is_wua = fields.Boolean(
        string='Part of WUA infrastructure?',
        default=False,
        readonly=True)

    infrastructure_type = fields.Selection(
        [('01_general', 'General Infrastructure'),
         ('02_pressurized', 'Pressurized Irrigation'),
         ('03_gravity', 'Gravity Irrigation')],
        string='Infrastructure Type',
        readonly=True,)

    is_primary = fields.Boolean(
        string='Primary infrastructure?',
        default=False,
        readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         _('Maintenance category already exists.')),
    ]

    @api.multi
    def unlink(self):
        for record in self:
            if record and record.is_wua:
                raise ValidationError(_(
                    'Cannot delete a WUA infrastructure category.'))
        res = super(WuaMaintenanceEquipmentCategory, self).unlink()
        return res
