# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    agriculturalseasons = \
        env['wua.agriculturalseason'].search([])
#   Method create of agriculturalseason created 12 registers, old ones don't
#   have the agriculturalseasons_month created
#   Thats the reason is used on post-migration
    for agriculturalseason in agriculturalseasons:
        if (len(agriculturalseason.agriculturalseason_month_ids) < 12):
            for month in range(1, 13):
                env['wua.agriculturalseason.month'].create({
                    'agriculturalseason_id': agriculturalseason.id,
                    'month': month
                    })
