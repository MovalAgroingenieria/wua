# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    attachment_model = env['maintenance.request.attachment']
    records = attachment_model.search([])
    for record in records:
        if record.image and record.filename:
            attachment = env['ir.attachment'].search([
                ('res_model', '=', 'maintenance.request.attachment'),
                ('res_id', '=', record.id),
                ('res_field', '=', 'image'),
            ], limit=1)
            if attachment:
                attachment.write({
                    'name': record.filename,
                    'datas_fname': record.filename,
                    'filename': record.filename,
                })
