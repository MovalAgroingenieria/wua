# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_negative_reading = env['wua.negative.reading'].search([])
    for n_reading in all_negative_reading:
        # All negative readings until migration can only be from remote control
        n_reading.from_remotecontrol = True
