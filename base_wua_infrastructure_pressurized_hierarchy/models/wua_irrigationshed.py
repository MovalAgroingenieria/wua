# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        ondelete='restrict')

    @api.constrains('hydraulicsector_id', 'waterpipe_id')
    def _check_waterpipe_id(self):
        if len(self) == 1:
            if self.hydraulicsector_id and self.waterpipe_id \
                    and self.hydraulicsector_id != \
                    self.waterpipe_id.hydraulicsector_id:
                raise exceptions.ValidationError(
                    _('The hydraulic sector of the water-pipe is not the '
                      'same as the hydraulic sector of the irrigation '
                      'shed.'))
