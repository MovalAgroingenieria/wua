# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.execute("""
            UPDATE wua_hydricmovement wh1
                SET invoiced_hydricmovement = CASE
                    WHEN EXISTS (
                        SELECT 1 FROM account_invoice_line ail
                        WHERE ail.hydricmovement_id = wh1.id
                    ) THEN TRUE
                    ELSE FALSE
                END;
            """)
        env.cr.execute("""
            UPDATE wua_hydricmovement wh1
                SET invoiceset_id = a.max_invoiceset_id
                FROM (
                    SELECT ail.hydricmovement_id AS hydricmovement_id,
                        MAX(ail.invoiceset_id) AS max_invoiceset_id
                    FROM account_invoice_line ail
                    GROUP BY ail.hydricmovement_id
                ) AS a
                WHERE wh1.id = a.hydricmovement_id
            """)
        env.cr.execute("""
            UPDATE wua_presconsumption wp1
                SET invoiced_consumption_quota = a.has_invoiced_hydricmovement
                FROM (
                    SELECT
                        wh1.presconsumption_id,
                        CASE WHEN COUNT(*) > 0 THEN TRUE ELSE FALSE END AS
                            has_invoiced_hydricmovement
                    FROM wua_hydricmovement wh1
                    WHERE wh1.invoiced_hydricmovement
                    GROUP BY wh1.presconsumption_id
                ) AS a
                WHERE wp1.id = a.presconsumption_id
            """)
        env.cr.execute("""
            UPDATE wua_irrigationreport wi1
                SET invoiced_irrigationreport_quota =
                    a.has_invoiced_hydricmovement
                FROM (
                    SELECT
                        wh1.irrigationreport_id,
                        CASE WHEN COUNT(*) > 0 THEN TRUE ELSE FALSE END AS
                            has_invoiced_hydricmovement
                    FROM wua_hydricmovement wh1
                    WHERE wh1.invoiced_hydricmovement
                    GROUP BY wh1.irrigationreport_id
                ) AS a
                WHERE wi1.id = a.irrigationreport_id
            """)
    except Exception as e:
        pass