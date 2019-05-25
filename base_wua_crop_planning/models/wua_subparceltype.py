# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaSubparceltype(models.Model):
    _inherit = 'wua.subparceltype'

    is_read_only = fields.Boolean(
        string='Read Only',
        default=False)

    @api.multi
    def unlink(self):
        for record in self:
            if record.is_read_only:
                raise exceptions.UserError(_(
                    'You cannot delete this subparcel type.'))
        return super(WuaSubparceltype, self).unlink()
