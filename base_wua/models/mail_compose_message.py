# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def onchange_template_id(
            self, template_id, composition_mode, model, res_id):
        if template_id and model == 'account.invoice' and res_id:
            invoice = self.env['account.invoice'].browse(res_id)
            lang = invoice.partner_id.lang
            if lang:
                self = self.with_context(lang=lang)
        return super(MailComposeMessage, self).onchange_template_id(
            template_id, composition_mode, model, res_id
        )
