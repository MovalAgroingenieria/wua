# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    mail_template_action = env.ref(
        'base_wua_quota_management.'
        'quota_notice_partner_report_email_template')
    mail_template_action.create_action()
