# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_watermeters = env['wua.watermeter'].search([])
    all_watermeters._compute_average_consumption()
    all_presconsumptions = env['wua.presconsumption'].search([])
    all_presconsumptions._compute_volume_perunitarea()
