# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WuaCertificate(models.Model):
    _inherit = 'wua.certificate'

    def _default_certificateuser_ids(self):
        resp = []
        model_wua_certificate = self.env['ir.model'].search(
            [('model', '=', 'wua.certificate')])
        if model_wua_certificate:
            model_id = model_wua_certificate[0].id
            user_ids = []
            reportcertificates = self.env['report.certificate'].search(
                [('model_id', '=', model_id), ('user_id', '!=', False)])
            for reportcertificate in (reportcertificates or []):
                user_ids.append(reportcertificate.user_id.id)
            if user_ids:
                user_ids = list(set(user_ids))
                for user_id in user_ids:
                    resp.append((0, 0, {'user_id': user_id, }))
        return resp

    certificateuser_ids = fields.One2many(
        string='Associated Signers',
        comodel_name='wua.certificate.user',
        inverse_name='certificate_id',
        default=_default_certificateuser_ids)

    signers = fields.Char(
        string='Signers',
        compute='_compute_signers')

    number_of_confirmed_signatures = fields.Integer(
        string='Number of confirmed signatures',
        default=0,
        compute='_compute_number_of_confirmed_signatures')

    number_of_confirmed_signatures_as_char = fields.Char(
        string='Number of confirmed signatures (as char)',
        compute='_compute_number_of_confirmed_signatures_as_char')

    current_user_can_sign = fields.Boolean(
        string='The user can sign',
        default=False,
        compute='_compute_current_user_can_sign')

    current_user_can_revoke = fields.Boolean(
        string='The user can revoke the signature',
        default=False,
        compute='_compute_current_user_can_revoke')

    @api.multi
    def _compute_signers(self):
        for record in self:
            signers = ''
            if record.certificateuser_ids:
                for certificateuser in record.certificateuser_ids:
                    signers = signers + ', ' + \
                        certificateuser.sudo().user_id.partner_id.display_name
            if signers:
                signers = signers[2:]
            record.signers = signers

    @api.multi
    def _compute_number_of_confirmed_signatures(self):
        for record in self:
            number_of_confirmed_signatures = 0

            if record.certificateuser_ids:
                for certificateuser in record.certificateuser_ids:
                    if certificateuser.signed:
                        number_of_confirmed_signatures = \
                            number_of_confirmed_signatures + 1
            record.number_of_confirmed_signatures = \
                number_of_confirmed_signatures

    @api.multi
    def _compute_number_of_confirmed_signatures_as_char(self):
        for record in self:
            number_of_confirmed_signatures_as_char = ''
            if record.number_of_confirmed_signatures > 0:
                number_of_confirmed_signatures_as_char = \
                    str(record.number_of_confirmed_signatures)
            record.number_of_confirmed_signatures_as_char = \
                number_of_confirmed_signatures_as_char

    @api.multi
    def _compute_current_user_can_sign(self):
        for record in self:
            current_user_can_sign = False
            if record.certificateuser_ids:
                for certificateuser in record.certificateuser_ids:
                    if (certificateuser.user_id == record.current_user_id and
                       (not certificateuser.signed)):
                        current_user_can_sign = True
                        break
            record.current_user_can_sign = current_user_can_sign

    @api.multi
    def _compute_current_user_can_revoke(self):
        for record in self:
            current_user_can_revoke = False
            if record.certificateuser_ids:
                for certificateuser in record.certificateuser_ids:
                    if (certificateuser.user_id == record.current_user_id and
                       certificateuser.signed):
                        current_user_can_revoke = True
                        break
            record.current_user_can_revoke = current_user_can_revoke

    @api.multi
    def action_sign_certificate(self):
        self.ensure_one()
        if (self.certificateuser_ids and self.state == '01_draft'):
            sign_ok = False
            for certificateuser in self.certificateuser_ids:
                if (certificateuser.user_id == self.current_user_id and
                   (not certificateuser.signed)):
                    if (self.current_user_id.has_group(
                       'base_wua.group_wua_manager')):
                        certificateuser.signed = True
                    else:
                        certificateuser.sudo().signed = True
                    sign_ok = True
                    break
            if sign_ok:
                all_signatures_ok = True
                for certificateuser in self.certificateuser_ids:
                    if not certificateuser.signed:
                        all_signatures_ok = False
                        break
                if all_signatures_ok:
                    if (self.current_user_id.has_group(
                       'base_wua.group_wua_manager')):
                        self.action_validate_certificate()
                    else:
                        self.sudo().action_validate_certificate()

    @api.multi
    def action_revoke_sign_certificate(self):
        self.ensure_one()
        if (self.certificateuser_ids and self.state == '01_draft'):
            for certificateuser in self.certificateuser_ids:
                if (certificateuser.user_id == self.current_user_id and
                   certificateuser.signed):
                    if (self.current_user_id.has_group(
                       'base_wua.group_wua_manager')):
                        certificateuser.signed = False
                    else:
                        certificateuser.sudo().signed = False
                    break

    def action_cancel_certificate(self):
        super(WuaCertificate, self).action_cancel_certificate()
        self._initialize_certificate_ids(init_value=False)

    @api.multi
    def _initialize_certificate_ids(self, init_value=False):
        for record in self:
            if record.certificateuser_ids:
                certificateusers = self.env['wua.certificate.user'].browse(
                    record.certificateuser_ids.ids)
                certificateusers.write({'signed': init_value})

    # Implemented hook.
    def _allowed_signature(self, certificate):
        resp = False
        if (certificate.certificateuser_ids and
           certificate.state == '01_draft'):
            for certificateuser in certificate.certificateuser_ids:
                certificateuser.sudo().signed = True
            resp = True
        return resp


class WuaCertificateUser(models.Model):
    _name = 'wua.certificate.user'
    _description = 'Signer of a certificate'
    _order = 'name'

    SIZE_NAME = 71

    certificate_id = fields.Many2one(
        string='Certificate',
        comodel_name='wua.certificate',
        required=True,
        index=True,
        ondelete='cascade')

    user_id = fields.Many2one(
        string='Signer',
        comodel_name='res.users',
        required=True,
        index=True,
        domain="[('share','=',False)]",
        ondelete='restrict')

    name = fields.Char(
        string='Certificate Signer',
        size=SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    signed = fields.Boolean(
        string='Signed',
        default=False,)

    signature_time = fields.Datetime(
        string='Signature Time',
        store=True,
        compute='_compute_signature_time')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Certificate-Signer.'),
        ]

    @api.depends('certificate_id', 'certificate_id.name',
                 'user_id', 'user_id.partner_id', 'user_id.partner_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.certificate_id and record.certificate_id.name and
               record.user_id and record.user_id.partner_id and
               record.user_id.partner_id.name):
                name = record.certificate_id.name + '-' + \
                    record.user_id.partner_id.name
            record.name = name

    @api.depends('signed')
    def _compute_signature_time(self):
        for record in self:
            signature_time = None
            if record.signed:
                signature_time = datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
            record.signature_time = signature_time
