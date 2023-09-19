# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaDraingevalve(models.Model):
    _inherit = 'wua.drainagevalve'

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        comodel_name='wua.waterpipe',
        index=True,
    )

    @api.onchange('waterpipe_id')
    def _onchange_waterpipe_id(self):
        if (self.waterpipe_id):
            self.hydraulicsector_id = self.waterpipe_id.hydraulicsector_id

    @api.model
    def create(self, vals):
        if 'waterpipe_id' in vals:
            if vals['waterpipe_id']:
                wp = self.env['wua.waterpipe'].browse(vals['waterpipe_id'])
                vals['hydraulicsector_id'] = wp.hydraulicsector_id.id
        return super(WuaDraingevalve, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'waterpipe_id' in vals:
            if vals['waterpipe_id']:
                wp = self.env['wua.waterpipe'].browse(vals['waterpipe_id'])
                vals['hydraulicsector_id'] = wp.hydraulicsector_id.id
        return super(WuaDraingevalve, self).write(vals)
