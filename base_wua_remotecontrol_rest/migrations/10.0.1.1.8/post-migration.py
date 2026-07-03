# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_wua_remotecontrol_rest.hooks import (
    install_cron_exclusions)


def migrate(cr, installed_version):
    """Retrofit cron exclusion setup on instances where migrations 1.1.6 and
    1.1.7 did not execute (function was named post_migrate instead of
    migrate).
    """
    install_cron_exclusions(cr)
