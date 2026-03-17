# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.wua_mdm_sensor_management.hooks import (
    create_performance_indexes,
)


def migrate(cr, version):
    create_performance_indexes(cr)
