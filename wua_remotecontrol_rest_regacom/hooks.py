# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Post-install hook to initialize regacom_position from position field
    for all water connections with regacom telecontrol
    """
    _logger.info('Initializing regacom_position from position field...')
    # Update regacom_position for all waterconnections with telecontrol
    # regacom
    cr.execute("""
        UPDATE wua_waterconnection
        SET regacom_position = position
        WHERE position IS NOT NULL
          AND (regacom_position IS NULL OR regacom_position = 0)
    """)
    updated_count = cr.rowcount
    _logger.info(
        'Updated %s water connections with regacom_position from position',
        updated_count,
    )
