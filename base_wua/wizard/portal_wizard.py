# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tools.translate import _
from odoo.exceptions import UserError

from odoo import api, models

_logger = logging.getLogger(__name__)


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    @api.multi
    def _send_email(self):
        if not self.env.user.email:
            raise UserError(
                _('You must have an email address in your User Preferences to '
                  'send emails.'))
        template = self.env.ref('base_wua.mail_template_data_new_portal_user')
        for wizard_line in self:
            lang = wizard_line.user_id.lang
            partner = wizard_line.user_id.partner_id
            portal_url = partner.with_context(
                signup_force_type_in_url='', lang=lang
                )._get_signup_url_for_action()[partner.id]
            partner.signup_prepare()
            if template:
                template.with_context(
                    dbname=self._cr.dbname, portal_url=portal_url, lang=lang
                    ).send_mail(wizard_line.id, force_send=True)
            else:
                _logger.warning('No email template found for sending email to '
                                'the portal user')
        return True
