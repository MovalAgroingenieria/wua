# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ReportCertificate(models.Model):
    _inherit = 'report.certificate'

    user_id = fields.Many2one(
        string='Signer',
        comodel_name='res.users',
        domain="[('share','=',False)]",
        ondelete='restrict')

    @api.model
    def create(self, vals):
        model_id = 0
        user_id = 0
        if 'model_id' in vals and vals['model_id']:
            model_id = vals['model_id']
        if 'user_id' in vals and vals['user_id']:
            user_id = vals['user_id']
        if user_id and model_id:
            model_name = self.env['ir.model'].browse(model_id).model
            if model_name != 'wua.certificate':
                raise exceptions.UserError(
                    _('It is only possible to enter a signer for the '
                      'certificate model.'))
        return super(ReportCertificate, self).create(vals)

    @api.multi
    def write(self, vals):
        model_id = 0
        user_id = 0
        if 'model_id' in vals:
            if vals['model_id']:
                model_id = vals['model_id']
        else:
            model_id = self.model_id.id
        if 'user_id' in vals:
            if vals['user_id']:
                user_id = vals['user_id']
        else:
            user_id = self.user_id.id
        if user_id and model_id:
            model_name = self.env['ir.model'].browse(model_id).model
            if model_name != 'wua.certificate':
                raise exceptions.UserError(
                    _('It is only possible to enter a signer for the '
                      'certificate model.'))
        super(ReportCertificate, self).write(vals)
        return True
