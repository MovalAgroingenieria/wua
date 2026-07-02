# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_wua_remotecontrol_rest.hooks import (
    install_cron_exclusions)


def post_migrate(cr, version):
    """Re-run cron exclusion setup in case 10.0.1.1.6 ran before the
    install_cron_exclusions helper existed in hooks.py."""
    install_cron_exclusions(cr)
