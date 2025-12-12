# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fix irrigation events crossing midnight (end_date < start_date)."""
    cr.execute("""
        SELECT COUNT(*)
        FROM wua_waterconnection_irrigation_event
        WHERE irrigation_end_date < irrigation_start_date
    """)
    affected_count = cr.fetchone()[0]
    if affected_count == 0:
        return
    cr.execute("""
        UPDATE wua_waterconnection_irrigation_event
        SET irrigation_end_date = irrigation_end_date + INTERVAL '1 day'
        WHERE irrigation_end_date < irrigation_start_date
    """)
    _logger.info('Fixed %s irrigation events crossing midnight',
                 affected_count)
