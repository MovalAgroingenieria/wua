# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base_wua_invoicing.hooks import create_performance_indexes


def migrate(cr, version):
    """Create performance indexes on upgrade for existing instances."""
    create_performance_indexes(cr)
