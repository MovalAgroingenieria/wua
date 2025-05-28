# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    maintenance_model = env['maintenance.request']
    attachment_model = env['maintenance.request.attachment']
    records = maintenance_model.search([
        '|',
        '|',
        ('resolution_image_before', '!=', False),
        ('resolution_image_after', '!=', False),
        ('field_image', '!=', False),
    ])
    for rec in records:
        if rec.resolution_image_before:
            attachment_model.create({
                'maintenance_id': rec.id,
                'image_type': 'before',
                'image': rec.resolution_image_before,
                'filename':
                    rec.resolution_image_before_filename or 'before.jpg',
            })
        if rec.resolution_image_after:
            attachment_model.create({
                'maintenance_id': rec.id,
                'image_type': 'after',
                'image': rec.resolution_image_after,
                'filename': rec.resolution_image_after_filename or 'after.jpg',
            })
        if rec.field_image:
            attachment_model.create({
                'maintenance_id': rec.id,
                'image_type': 'field',
                'image': rec.field_image,
                'filename': 'field.jpg',
            })
        rec.write({
            'resolution_image_before': False,
            'resolution_image_before_filename': False,
            'resolution_image_after': False,
            'resolution_image_after_filename': False,
            'field_image': False,
        })
