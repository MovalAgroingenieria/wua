# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    # Empty, inherit and added by Hook
    telecontrol_associated = fields.Selection(
        selection_add=[('regacom', 'Regacom')],
    )

    regacom_position = fields.Integer(
        string='Regacom Position',
        help='Position identifier for Regacom database synchronization',
    )

    @api.model
    def create(self, vals):
        # Set regacom_position default from position if not provided
        if 'regacom_position' not in vals and 'position' in vals:
            vals['regacom_position'] = vals['position']
        return super(WuaWaterconnection, self).create(vals)

    @api.onchange('position')
    def _onchange_position(self):
        if self.position:
            self.regacom_position = self.position

    @api.onchange('telecontrol_associated')
    def _onchange_telecontrol_associated(self):
        # When telecontrol is changed to regacom, copy position to
        # regacom_position
        if self.telecontrol_associated == 'regacom' and self.position:
            self.regacom_position = self.position
