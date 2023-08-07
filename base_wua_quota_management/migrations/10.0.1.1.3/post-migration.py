# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Recompute name
    ima = env['wua.individualinput.massive.assignment'].search([])
    ima._compute_name()
    # Recompute name (May not be necessary because compute name of the line
    # depends on the parent name, but better ensure)
    imal = env['wua.individualinput.massive.assignment.line'].search([])
    imal._compute_name()
