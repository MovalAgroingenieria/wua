# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardImagePreview(models.TransientModel):
    _name = 'wizard.image.preview'

    name = fields.Char(
        readonly=True,
    )
    image_ids = fields.Many2many(
        comodel_name='maintenance.request.attachment',
        readonly=True,
    )
    current_index = fields.Integer(
        default=0,
    )
    image = fields.Binary(
        compute='_compute_current_image',
        readonly=True,
    )

    show_prev = fields.Boolean(
        compute='_compute_show_buttons',
        readonly=True,
    )
    show_next = fields.Boolean(
        compute='_compute_show_buttons',
        readonly=True,
    )

    @api.depends('image_ids', 'current_index')
    def _compute_current_image(self):
        for record in self:
            if (
                record.image_ids and
                0 <= record.current_index < len(record.image_ids)
            ):
                record.image = record.image_ids[record.current_index].image
                record.name = record.image_ids[record.current_index].filename
            else:
                record.image = False
                record.name = False

    @api.depends('current_index', 'image_ids')
    def _compute_show_buttons(self):
        for record in self:
            record.show_prev = record.current_index > 0
            record.show_next = \
                (record.image_ids and
                 record.current_index < len(record.image_ids) - 1)

    def action_next_image(self):
        for record in self:
            if record.current_index + 1 < len(record.image_ids):
                record.current_index += 1
        return {'type': 'ir.actions.act_window_reload'}

    def action_prev_image(self):
        for record in self:
            if record.current_index > 0:
                record.current_index -= 1
        return {'type': 'ir.actions.act_window_reload'}
