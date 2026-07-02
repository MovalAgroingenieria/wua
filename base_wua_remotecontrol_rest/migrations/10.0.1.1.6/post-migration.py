# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo.addons.base_wua_remotecontrol_rest.hooks import (
    install_cron_exclusions)

_logger = logging.getLogger(__name__)


def post_migrate(cr, version):
    """Install mutual exclusion between all remote-control import crons.

    All four crons write to wua_waterconnection (either directly or via
    stored computed fields).  Running any two simultaneously risks row-level
    lock contention and deadlocks.

    The post_init_hook handles fresh installs.  This migration retrofits
    existing databases where the cron records already exist with
    noupdate=1 in ir_model_data.
    """
    install_cron_exclusions(cr)
