# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        UPDATE wua_presconsumption
        SET invoiced_consumption_quota = TRUE WHERE id IN
        (SELECT DISTINCT(wp1.id) FROM wua_presconsumption wp1
            INNER JOIN wua_hydricmovement wh1 ON wp1.id =
            wh1.presconsumption_id WHERE
            wh1.invoiced_hydricmovement)
        """)
    env.cr.execute("""
        UPDATE wua_reading
        SET invoiced_reading_quota = TRUE WHERE id IN
        (SELECT DISTINCT(wr1.id) FROM wua_reading wr1
            INNER JOIN wua_presconsumption wp1 ON wp1.id =
            wr1.presconsumption_id WHERE
            wp1.invoiced_consumption_quota)
        """)
