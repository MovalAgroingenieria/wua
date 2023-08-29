# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFertconsumption(models.Model):
    _inherit = 'wua.fertconsumption'

    fertconsumptionset_id = fields.Many2one(
        string='Fertconsumption Set',
        comodel_name='wua.fertconsumptionset',
        ondelete='set null',
        readonly=True,
    )

    @api.multi
    def unlink(self):
        for record in self:
            if (record.fertconsumptionset_id and not self.env.context.get(
                    'force_unlink', False)):
                raise exceptions.UserError(_(
                    'You cannot delete a fertconsumption related with a '
                    'fertconsumption set, cancel it instead.'))
        return super(WuaFertconsumption, self).unlink()
