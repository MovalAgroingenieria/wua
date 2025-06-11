# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    kinds = env['maintenance.kind'].search([])

    for kind in kinds:
        value = kind.images_required
        kind.image_before_required = value
        kind.image_after_required = value
