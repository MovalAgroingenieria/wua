# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    for_shp_generation = fields.Boolean(
        string='File to being included on SHP generation',
        default=False,
    )

    @api.model
    def create(self, vals):
        for_shp_generation = self._context.get('for_shp_generation', False)
        if for_shp_generation:
            vals['for_shp_generation'] = for_shp_generation
        return super(IrAttachment, self).create(vals)
