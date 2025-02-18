# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Dropping ir_values of qr data")
    try:
        cr.execute("""
            DELETE FROM ir_values WHERE name = 'add_qr_code_in_attendance
            AND model = 'wua.assembly.configuration';';
        """)
        _logger.info("ir_values of qr data dropped successfully.")
    except Exception as e:
        _logger.error("Error dropping ir_values of qr data)")