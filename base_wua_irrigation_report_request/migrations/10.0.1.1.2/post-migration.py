# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    update_report_requests(env)


def update_report_requests(env,):
    reportrequest_model = env['wua.reportrequest']
    all_reportrequests = reportrequest_model.search([])
    for report in all_reportrequests:
        if not report.intake_id:
            intake_id = None
            if report.irrigationreport_id:
                intake_id = report.irrigationreport_id.intake_id
            else:
                intake_ids = env['wua.intake'].search(
                    [('product_id', '=', report.product_id.id)])
                if intake_ids:
                    intake_id = intake_ids[0]
            report.intake_id = intake_id
