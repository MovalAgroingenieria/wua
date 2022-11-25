# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from datetime import datetime


class ResFile(models.Model):
    _inherit = 'res.file'

    parcellink_ids = fields.One2many(
        string='Parcels',
        comodel_name='res.file.parcellink',
        inverse_name='file_id',
        track_visibility='onchange')

    has_parcellinks = fields.Boolean(
        string='Has parcellinks',
        default=False,
        compute="_compute_has_parcellinks",)

    @api.depends('parcellink_ids')
    def _compute_has_parcellinks(self):
        for record in self:
            has_parcellinks = False
            if record.parcellink_ids:
                has_parcellinks = True
            record.has_parcellinks = has_parcellinks

    @api.constrains('parcellink_ids')
    def _check_parcellink_ids(self):
        if len(self) == 1:
            file = self
            unique_ids_of_parcel = []
            for parcellink in file.parcellink_ids:
                unique_ids_of_parcel.append(parcellink.parcel_id.id)
            unique_ids_of_parcel = list(set(unique_ids_of_parcel))
            if len(unique_ids_of_parcel) != len(file.parcellink_ids):
                raise exceptions.UserError(_('There are repeated parcels.'))

    @api.multi
    def action_generate_parcels_shp(self):
        for record in self:
            parcels = record.parcellink_ids.mapped(lambda x: x.parcel_id)
            result = parcels.generate_parcel_shp()
            attachment_obj = self.sudo().env['ir.attachment']
            parcel_label = _('Parcels')
            current_date = datetime.now()
            filename = parcel_label + '_' + current_date.strftime('%Y-%m-%d')
            # create attachment, add timestamp or something here?
            attachment_obj.create(
                {'name': filename, 'datas_fname': filename,
                 'datas': result, 'res_id': record.id, 'res_model': 'res.file'}
            )

    @api.multi
    def action_get_partner_parcels(self):
        if not self.partner_id:
            raise exceptions.UserError(_(
                'No main partner has been selected for this file.'))
        if self.parcellink_ids:
            raise exceptions.UserError(_(
                'If a file already has parcels, this operation is not '
                'possible.'))
        parcels = self.env['wua.parcel'].search(
            [('partner_id', '=', self.partner_id.id)])
        for parcel in parcels:
            self.env['res.file.parcellink'].create({
                'file_id': self.id,
                'parcel_gis_viewer_link': parcel.gis_viewer_link,
                'parcel_cadastral_reference_link':
                    parcel.cadastral_reference_link,
                'parcel_id': parcel.id,
                'parcel_area_official': parcel.area_official,
                'parcel_rural_location_county': parcel.rural_location_county,
                'parcel_cadastral_reference': parcel.cadastral_reference,
                'parcel_partner_id': parcel.partner_id.id,
            })


class ResFileParcellink(models.Model):
    _name = 'res.file.parcellink'

    file_id = fields.Many2one(
        string='File_',
        comodel_name='res.file',
        required=True,
        index=True,
        ondelete='cascade')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='restrict')

    parcel_area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        store=True,
        compute='_compute_parcel_area_official')

    parcel_rural_location_county = fields.Char(
        string='Location',
        store=True,
        compute='_compute_parcel_rural_location_county')

    parcel_cadastral_reference = fields.Char(
        string='Cadastral Reference',
        store=True,
        compute='_compute_parcel_cadastral_reference')

    parcel_partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict',
        store=True,
        compute='_compute_parcel_partner_id')

    parcel_gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_parcel_gis_viewer_link')

    parcel_cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_parcel_cadastral_reference_link')

    subject = fields.Char(
        string='Subject',
        related='file_id.subject')

    category_id = fields.Many2one(
        string='Category',
        related='file_id.category_id')

    @api.multi
    def _compute_parcel_gis_viewer_link(self):
        for record in self:
            if record.parcel_id:
                record.parcel_gis_viewer_link = \
                    record.parcel_id.gis_viewer_link

    @api.multi
    def _compute_parcel_cadastral_reference_link(self):
        for record in self:
            if record.parcel_id:
                record.parcel_cadastral_reference_link = \
                    record.parcel_id.cadastral_reference_link

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.parcel_gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.parcel_gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_see_cadastral_report(self):
        self.ensure_one()
        if self.parcel_cadastral_reference_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.parcel_cadastral_reference_link,
                'target': 'new',
            }

    @api.depends('parcel_id')
    def _compute_parcel_area_official(self):
        for record in self:
            if record.parcel_id:
                record.parcel_area_official = \
                    record.parcel_id.area_official

    @api.depends('parcel_id')
    def _compute_parcel_rural_location_county(self):
        for record in self:
            if record.parcel_id:
                record.parcel_rural_location_county = \
                    record.parcel_id.rural_location_county

    @api.depends('parcel_id')
    def _compute_parcel_cadastral_reference(self):
        for record in self:
            if record.parcel_id:
                record.parcel_cadastral_reference = \
                    record.parcel_id.cadastral_reference

    @api.depends('parcel_id')
    def _compute_parcel_partner_id(self):
        for record in self:
            if record.parcel_id:
                record.parcel_partner_id = record.parcel_id.partner_id
