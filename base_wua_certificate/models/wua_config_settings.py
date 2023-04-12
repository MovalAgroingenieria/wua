# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    sequence_certificate_code_id = fields.Many2one(
        string='Sequence for certificate coding',
        comodel_name='ir.sequence',
        help='It is mandatory to enter this parameter to activate '
             'the certificate management')

    only_parcels_as_main = fields.Boolean(
        string='Only parcels as main',
        default=False,
        help='Add to the certificate the parcel only if the partner is the '
             'main partner of the parcel')

    default_certificatetype_id = fields.Many2one(
        string='Default certificate type',
        comodel_name='wua.certificate.type',
        help='Before creating a certificate, this is the type that the '
             'program will propose by default')

    allowed_request_for_portal_user = fields.Boolean(
        string='Allowed request for portal user',
        default=True,
        help='Activate this parameter to allow portal users to request '
             'certificates')

    portaluser_certificatetype_id = fields.Many2one(
        string='Certificate type for portal users',
        comodel_name='wua.certificate.type',
        help='For portal users, restrict the certificate type')

    max_pending_certificates = fields.Integer(
        string='Maximun number of pending certificates',
        default=1,
        help='For portal users, maximun number of not-validated certificates')

    ip_remote_address = fields.Char(
        string='Allowed remote IP for public HTTP-GET',
        size=30,
        default='127.0.0.1',
        help='For public creation of certificates based on HTTP-GET '
             'requests, restriction to clientes from a IP address')

    use_intersected_area = fields.Boolean(
        string='Use intersected Area on Certificates',
        default=False,
        help='Activate this parameter to use the intersected area on the '
             'certificates instead of the official area')

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.configuration',
                           'sequence_certificate_code_id',
                           self.sequence_certificate_code_id.id)
        values.set_default('wua.configuration',
                           'only_parcels_as_main',
                           self.only_parcels_as_main)
        values.set_default('wua.configuration',
                           'default_certificatetype_id',
                           self.default_certificatetype_id.id)
        values.set_default('wua.configuration',
                           'allowed_request_for_portal_user',
                           self.allowed_request_for_portal_user)
        values.set_default('wua.configuration',
                           'portaluser_certificatetype_id',
                           self.portaluser_certificatetype_id.id)
        values.set_default('wua.configuration',
                           'max_pending_certificates',
                           self.max_pending_certificates)
        values.set_default('wua.configuration',
                           'use_intersected_area',
                           self.use_intersected_area)
        values.set_default('wua.configuration',
                           'ip_remote_address',
                           self.ip_remote_address)
