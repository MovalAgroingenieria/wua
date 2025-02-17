# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Dropping SQL view: wua_quota_aggregatevalue")
    try:
        cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS
            wua_quota_aggregatevalue CASCADE;
        """)
        cr.execute("""
            DROP INDEX IF EXISTS idx_wua_quota_aggregatevalue;""")
        _logger.info("SQL view wua_quota_aggregatevalue dropped successfully.")
    except Exception as e:
        _logger.error("Error dropping SQL view wua_quota_aggregatevalue)")
