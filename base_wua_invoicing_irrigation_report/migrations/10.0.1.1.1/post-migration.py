# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    irrigation_reports = \
        env['wua.irrigationreport'].search([('product_id', '!=', False)])
    for report in irrigation_reports:
        if report.product_id:
            report.price_unit = report.product_id.lst_price
    env.cr.commit()
