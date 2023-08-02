# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    telecontrol_failed_template_id = env.ref(
        'base_wua_remotecontrol_rest.'
        'telecontrol_failed_email_template').id
    mail_template = env['mail.template'].browse(
        telecontrol_failed_template_id)
    mail_server = env['ir.mail_server'].sudo().search([], limit=1)
    if mail_server:
        mail_template.email_from = "Telecontrol Management <" + mail_server.smtp_user + ">"
