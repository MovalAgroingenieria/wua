# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCertificate(models.Model):
    _inherit = 'wua.certificate'

    certificatesigpac_ids = fields.One2many(
        string='Associated SIGPAC Enclosures',
        comodel_name='wua.certificate.sigpac',
        inverse_name='certificate_id')

    @api.onchange('certificateparcel_ids')
    def _onchange_included_in_certificate(self):
        parcels = self.certificateparcel_ids
        for parcel in parcels:
            included = False
            if parcel.included_in_certificate:
                included = True
            for enclosure in parcel.certificatesigpac_ids:
                enclosure.write({
                    'included_in_certificate': included,
                    'enclosure_included_in_certificate': included})


class WuaCertificateParcel(models.Model):
    _inherit = 'wua.certificate.parcel'

    certificatesigpac_ids = fields.One2many(
        string='Associated SIGPAC Enclosures',
        comodel_name='wua.certificate.sigpac',
        inverse_name='certificateparcel_id')

    @api.model
    def create(self, vals):
        if 'parcel_id' in vals and vals['parcel_id']:
            parcel = self.env['wua.parcel'].browse(vals['parcel_id'])
            if parcel.sigpaclink_ids:
                vals['certificatesigpac_ids'] = []
                for sigpaclink in parcel.sigpaclink_ids:
                    vals_new_certificatesigpac = {
                        'sigpac_code': sigpaclink.sigpac_id.name,
                        'parcel_area': sigpaclink.parcel_area,
                        'area_ha': sigpaclink.area_ha,
                        'parcel_area': sigpaclink.parcel_area,
                        'intersection_percentage':
                            sigpaclink.intersection_percentage,
                        'coef_rega': sigpaclink.coef_rega,
                        'uso_sigpac': sigpaclink.uso_sigpac,
                        }
                    vals['certificatesigpac_ids'].append(
                        (0, 0, vals_new_certificatesigpac))
        return super(WuaCertificateParcel, self).create(vals)


class WuaCertificateSigpac(models.Model):
    _name = 'wua.certificate.sigpac'
    _description = 'SIGPAC enclosure of a certificate'
    _order = 'name'

    certificateparcel_id = fields.Many2one(
        string='Parcel of certificate',
        comodel_name='wua.certificate.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    sigpac_code = fields.Char(
        string='SIGPAC Code',)

    name = fields.Char(
        string='Register Code',
        store=True,
        index=True,
        compute='_compute_name')

    enclosure_number = fields.Integer(
        string='Enclosure Number',
        compute='_compute_enclosure_number',)

    certificate_id = fields.Many2one(
        string='Certificate',
        comodel_name='wua.certificate',
        store=True,
        index=True,
        ondelete='set null',
        compute='_compute_certificate_id')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        store=True,
        ondelete='set null',
        compute='_compute_parcel_id')

    parcel_area = fields.Float(
        string='GIS Area of parcel (m²)',
        digits=(32, 2),)

    area_ha = fields.Float(
        string='Area (ha)',
        digits=(32, 4),)

    parcel_area_ha = fields.Float(
        string='GIS Area of parcel (ha)',
        digits=(32, 4),
        compute='_compute_parcel_area_ha',)

    intersection_percentage = fields.Float(
        string='% in parcel',
        digits=(32, 2),)

    coef_rega = fields.Integer(
        string='Irrigation Coefficient (0-100)',)

    uso_sigpac = fields.Selection(
        string='Land Use',
        selection=[
            ('AG', 'AG - CORRIENTES Y SUPERFICIES DE AGUA'),
            ('CA', 'CA - VIALES'),
            ('CF', 'CF - ASOCIACIÓN CÍTRICOS-FRUTALES'),
            ('CI', 'CI - CITRICOS'),
            ('CS', 'CS - ASOCIACIÓN CÍTRICOS-FRUTALES DE CÁSCARA'),
            ('CV', 'CV - ASOCIACIÓN CÍTRICOS-VIÑEDO'),
            ('ED', 'ED - EDIFICACIONES'),
            ('EP', 'EP - ELEMENTO DEL PAISAJE'),
            ('FF', 'FF - ASOCIACIÓN FRUTALES-FRUTALES DE CÁSCARA'),
            ('FL', 'FL - FRUTOS SECOS Y OLIVAR'),
            ('FO', 'FO - FORESTAL'),
            ('FS', 'FS - FRUTOS SECOS'),
            ('FV', 'FV - FRUTOS SECOS Y VIÑEDO'),
            ('FY', 'FY - FRUTALES'),
            ('IM', 'IM - IMPRODUCTIVOS'),
            ('IV', 'IV - INVERNADEROS Y CULTIVOS BAJO PLASTICO'),
            ('MT', 'MT - MATORRAL'),
            ('OC', 'OC - ASOCIACIÓN OLIVAR-CÍTRICOS'),
            ('OF', 'OF - OLIVAR - FRUTAL'),
            ('OV', 'OV - OLIVAR'),
            ('PA', 'PA - PASTO CON ARBOLADO'),
            ('PR', 'PR - PASTO ARBUSTIVO'),
            ('PS', 'PS - PASTIZAL'),
            ('TA', 'TA - TIERRAS ARABLES'),
            ('TH', 'TH - HUERTA'),
            ('VF', 'VF - VIÑEDO - FRUTAL'),
            ('VI', 'VI - VIÑEDO'),
            ('VO', 'VO - VIÑEDO - OLIVAR'),
            ('ZC', 'ZC - ZONA CONCENTRADA NO INCLUIDA EN LA ORTOFOTO'),
            ('ZU', 'ZU - ZONA URBANA'),
            ('ZV', 'ZV - ZONA CENSURADA'),
        ],)

    included_in_certificate = fields.Boolean(
        string='Included',
        store=True,
        compute='_compute_included_in_certificate')

    enclosure_included_in_certificate = fields.Boolean(
        string='Enclosure included',
        store=True,
        readonly=False,
        compute='_compute_enclosure_included_in_certificate')

    @api.depends('certificateparcel_id', 'sigpac_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.certificateparcel_id and record.sigpac_code:
                name = record.certificateparcel_id.certificate_id.name + \
                    '-' + record.certificateparcel_id.parcel_id.name + \
                    '-' + record.sigpac_code
            record.name = name

    @api.multi
    def _compute_enclosure_number(self):
        for record in self:
            enclosure_number = 0
            if record.sigpac_code and len(record.sigpac_code) > 3:
                enclosure_number_as_str = record.sigpac_code[-3:]
                if enclosure_number_as_str.isdigit():
                    enclosure_number = int(enclosure_number_as_str)
            record.enclosure_number = enclosure_number

    @api.depends('certificateparcel_id')
    def _compute_certificate_id(self):
        for record in self:
            certificate_id = None
            if (record.certificateparcel_id and
               record.certificateparcel_id.certificate_id):
                certificate_id = record.certificateparcel_id.certificate_id
            record.certificate_id = certificate_id

    @api.depends('certificateparcel_id')
    def _compute_parcel_id(self):
        for record in self:
            parcel_id = None
            if (record.certificateparcel_id and
               record.certificateparcel_id.parcel_id):
                parcel_id = record.certificateparcel_id.parcel_id
            record.parcel_id = parcel_id

    @api.multi
    def _compute_parcel_area_ha(self):
        for record in self:
            record.parcel_area_ha = record.parcel_area / 10000

    @api.depends('certificateparcel_id',
                 'certificateparcel_id.included_in_certificate')
    def _compute_included_in_certificate(self):
        for record in self:
            included_in_certificate = False
            enclosure_included_in_certificate = False
            if (record.certificateparcel_id and
               record.certificateparcel_id.included_in_certificate):
                included_in_certificate = True
                enclosure_included_in_certificate = True
            record.included_in_certificate = included_in_certificate
            record.enclosure_included_in_certificate = \
                enclosure_included_in_certificate

    @api.depends('included_in_certificate')
    def _compute_enclosure_included_in_certificate(self):
        for record in self:
            enclosure_included_in_certificate = False
            if (record.included_in_certificate):
                enclosure_included_in_certificate = True
            record.enclosure_included_in_certificate = \
                enclosure_included_in_certificate
