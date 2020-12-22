# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    update_report_requests_number(env)


def update_report_requests_number(env,):
    sequence = env['ir.sequence'].search(
        [('code', '=', 'wua.cralhama.reportrequest.seq')])
    sequence_prefix = '2020/'
    sequence_number = sequence.number_next
    current_seq = sequence.prefix + str(sequence_number).zfill(4)
    reportrequests = env['wua.reportrequest'].search([])
    for report in reportrequests:
        if not report.reportrequest_number:
            sequence_number += 1
            current_seq = sequence_prefix + str(sequence_number).zfill(4)
            report.reportrequest_number = current_seq
