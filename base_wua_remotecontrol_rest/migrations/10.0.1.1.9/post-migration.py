# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    """Update telecontrol failed email template on existing databases."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = False

    _logger.info(
        'base_wua_remotecontrol_rest post-migration 10.0.1.1.9 started'
    )

    try:
        template = env.ref(
            'base_wua_remotecontrol_rest.telecontrol_failed_email_template'
        )
    except ValueError:
        _logger.warning(
            'Template telecontrol_failed_email_template was not found. '
            'No updates were applied.'
        )

    if template:
        template_values = {
            'name': 'Remote control failed',
            'email_from': '"Telecontrol Management" "<NULL>"',
            'email_to': 'monitoring@moval.es',
            'subject': ' Remote control has experienced some problem',
            'body_html': '<p/>',
        }
        template.write(template_values)
        _logger.info(
            'Template telecontrol_failed_email_template updated '
            'successfully.'
        )
