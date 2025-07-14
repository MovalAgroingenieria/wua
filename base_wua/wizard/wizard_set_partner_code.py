# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardSetPartnerCode(models.TransientModel):
    _name = 'wizard.set.partner.code'
    _description = 'Dialog box to set a Partner Code'

    partner_code = fields.Integer(
        string='Partner Code',)

    @api.model
    def default_get(self, var_fields):
        resp = None
        record = self.env['res.partner'].browse(
            self.env.context['active_id'])
        if record:
            last_code = self.env['res.partner'].search(
                [], order='partner_code desc', limit=1).partner_code
            resp = {
                'partner_code': last_code + 1 if last_code else 1,
            }
        return resp

    def set_partner_code(self):
        self.ensure_one()
        record = self.env['res.partner'].browse(
            self.env.context['active_id'])
        partner_code = self.partner_code
        if partner_code <= 0:
            raise UserError(_('The partner code '
                              'must be a positive value.'))
        elif record and not record.is_wua_partner:
            record.write({
                'is_wua_partner': True,
                'partner_code': partner_code,
                'customer': True,
            })
        else:
            raise UserError(
                _('Is not possible to change the partner_code '
                  'of a partner that is already a WUA partner'))
