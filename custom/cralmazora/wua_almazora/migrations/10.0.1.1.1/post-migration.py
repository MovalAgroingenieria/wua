# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    update_gross_amunt_in_gravconsumptions(env, version)


def update_gross_amunt_in_gravconsumptions(env, version):
    _logger = logging.getLogger(__name__)
    gravconsumptions = env['wua.gravconsumption'].search([])
    if gravconsumptions:
        gravconsumptions._compute_gross_amount()
        gravconsumptions._compute_area_irrigation()
        _logger.info('update_gross_amunt_in_gravconsumptions: ' +
                     str(len(gravconsumptions)) +
                     ' gravity consumptions updated.')
