# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    agriculturalseasons = \
        env['wua.agriculturalseason'].search([])
#   Method create of agriculturalseason created 12 registers, old ones don't
#   have the agriculturalseasons_month created
#   Thats the reason is used on post-migration
    for agriculturalseason in agriculturalseasons:
        if (not agriculturalseason.balance_id):
            start_date = agriculturalseason
            end_date = agriculturalseason
            initial_date_str = datetime.datetime.strptime(
                start_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                end_date, '%Y-%m-%d').strftime('%x')
            description = initial_date_str + ' - ' + end_date_str
            env['wua.intakeconsumption.balance'].create({
                'agriculturalseason_id': agriculturalseason.id,
                'balance_type': 'C',
                'description': description
                })
