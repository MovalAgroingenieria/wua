# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaIndividualinput(models.Model):
    _inherit = 'wua.individualinput'

    watertransfer_id = fields.Many2one(
        string='Water Transfer',
        comodel_name='wua.watertransfer',
        index=True,
        ondelete='restrict',)

    @api.multi
    def unlink(self):
        for record in self:
            if not self.env.context.get('force_unlink', False) and \
                    record.watertransfer_id:
                raise exceptions.UserError(
                    _('Cannot delete individual input associated with water '
                      'transfer, delete the water transfer instead.'))
        return super(WuaIndividualinput, self).unlink()
