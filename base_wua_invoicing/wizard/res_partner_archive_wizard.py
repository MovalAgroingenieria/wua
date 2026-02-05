# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartnerArchiveWizard(models.TransientModel):
    _name = 'res.partner.archive.wizard'
    _description = 'Confirm archiving supplier partners'

    partner_ids = fields.Many2many(
        'res.partner',
        string='Partners to Archive',
        readonly=True)

    message = fields.Html(
        string='Message',
        readonly=True,
        compute='_compute_message')

    @api.depends('partner_ids')
    def _compute_message(self):
        for wizard in self:
            if wizard.partner_ids:
                supplier_partners = wizard.partner_ids.filtered(lambda p: p.supplier)
                if supplier_partners:
                    partner_names = '<ul>'
                    for partner in supplier_partners:
                        partner_names += '<li><b>%s</b></li>' % partner.name
                    partner_names += '</ul>'

                    wizard.message = _(
                        '<p style="color: red; font-weight: bold;">'
                        'WARNING: You are about to archive the following suppliers:'
                        '</p>%s'
                        '<p>Are you sure you want to continue?</p>'
                    ) % partner_names
                else:
                    wizard.message = ''
            else:
                wizard.message = ''

    @api.multi
    def action_confirm_archive(self):
        self.ensure_one()
        if self.partner_ids:
            self.partner_ids.with_context(confirmed_archive=True).toggle_active()
        return {'type': 'ir.actions.act_window_close'}
