# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_migrate(cr, version):
    """Exclude the controlreading import cron from all remotecontrol crons.

    The post_init_hook handles fresh installs.  This migration retrofits
    existing databases.
    """
    from odoo.addons.base_wua_pressurized_irrigation_monitoring.hooks import (
        install_cron_exclusions)
    install_cron_exclusions(cr)
