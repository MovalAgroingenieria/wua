# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from datetime import datetime
from jinja2 import Template, TemplateError
from odoo import models, fields, api, exceptions, _


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

    category_is_lease = fields.Boolean(
        string='Category is lease',
        default=False,
        compute="_compute_category_is_lease")

    category_is_trading = fields.Boolean(
        string='Category is trading',
        default=False,
        compute="_compute_category_is_trading")

    leased_from = fields.Date(
        string="Lease from",
        track_visibility='onchange',
        index=True)

    leased_to = fields.Date(
        string="Lease to",
        track_visibility='onchange',
        index=True)

    partnerlink_lease_ids = fields.One2many(
        string='Partners',
        comodel_name='res.file.partnerlink',
        inverse_name='file_id')

    partnerlink_trading_ids = fields.One2many(
        string='Partners',
        comodel_name='res.file.partnerlink',
        inverse_name='file_id')

    category_report_id = fields.Many2one(
        string="Report",
        comodel_name='res.file.category.report')

    category_report_id_domain = fields.Char(
        readonly=True,
        compute="_compute_category_report_id_domain")

    template_start_rendered = fields.Html(
        string='Template start rendered',
        compute='_compute_template_start_rendered')

    template_end_rendered = fields.Html(
        string='Template end rendered',
        compute='_compute_template_end_rendered')

    @api.depends('partnerlink_lease_ids')
    def _insert_partnerlink_ids_from_lease(self):
        for record in self:
            if record.partnerlink_lease_ids:
                record.partnerlink_ids = record.partnerlink_lease_ids

    @api.depends('partnerlink_trading_ids')
    def _insert_partnerlink_ids_from_trading(self):
        for record in self:
            if record.partnerlink_trading_ids:
                record.partnerlink_ids = record.partnerlink_trading_ids

    @api.depends('parcellink_ids')
    def _compute_has_parcellinks(self):
        for record in self:
            has_parcellinks = False
            if record.parcellink_ids:
                has_parcellinks = True
            record.has_parcellinks = has_parcellinks

    @api.depends('category_id')
    def _compute_category_is_lease(self):
        for record in self:
            category_is_lease = False
            category_is_lease_id = self.env.ref(
                'wua_crm_filemgmt.resfilecategory_lease_file').id
            if record.category_id.id == category_is_lease_id:
                category_is_lease = True
            record.category_is_lease = category_is_lease

    @api.depends('category_id')
    def _compute_category_is_trading(self):
        for record in self:
            category_is_trading = False
            category_is_trading_id = self.env.ref(
                'wua_crm_filemgmt.resfilecategory_trading_file').id
            if record.category_id.id == category_is_trading_id:
                category_is_trading = True
            record.category_is_trading = category_is_trading

    @api.depends('category_id')
    def _compute_category_report_id_domain(self):
        for record in self:
            domain = False
            if record.category_id:
                domain = [('category_id', '=', record.category_id.id)]
            if domain:
                record.category_report_id_domain = json.dumps(domain)
            else:
                record.category_report_id_domain = False

    @api.depends('category_report_id',
                 'category_report_id.report_template_start')
    def _compute_template_start_rendered(self):
        for record in self:
            template_start_rendered = ''
            if (record.category_report_id and
                    record.category_report_id.report_template_start):
                try:
                    template_start = Template(
                        self.category_report_id.report_template_start)
                    template_start_rendered = \
                        template_start.render(record=record)
                except TemplateError as e:
                    template_start_rendered = \
                        '<p style="text-align:center;color:red;">' + \
                        '<b><font style="font-size: 14px;">' + \
                        _('ERROR IN START TEMPLATE') + '</font></b></p>' + \
                        '<p><br>' + e.message + '</p>'
            record.template_start_rendered = template_start_rendered

    @api.depends('category_report_id',
                 'category_report_id.report_template_end')
    def _compute_template_end_rendered(self):
        for record in self:
            template_end_rendered = ''
            if (record.category_report_id and
                    record.category_report_id.report_template_end):
                try:
                    template_end = Template(
                        self.category_report_id.report_template_end)
                    template_end_rendered = template_end.render(record=record)
                except TemplateError as e:
                    template_end_rendered = \
                        '<p style="text-align:center;color:red;">' + \
                        '<b><font style="font-size: 14px;">' + \
                        _('ERROR IN END TEMPLATE') + '</font></b></p>' + \
                        '<p><br>' + e.message + '</p>'
            record.template_end_rendered = template_end_rendered

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

    @api.multi
    def action_print_selected_report(self):
        self.ensure_one()
        report_name = ''
        if self.category_report_id.iractreportxml_id:
            report_name = self.category_report_id.iractreportxml_id.report_name
        return self.env['report'].with_context(
            {'lang': self.partner_id.lang}).get_action(
                self, report_name)

    @api.constrains('parcellink_ids')
    def _check_parcellink_ids(self):
        if len(self) == 1:
            current_file = self
            unique_ids_of_parcel = []
            for parcellink in current_file.parcellink_ids:
                unique_ids_of_parcel.append(parcellink.parcel_id.id)
            unique_ids_of_parcel = list(set(unique_ids_of_parcel))
            if len(unique_ids_of_parcel) != len(current_file.parcellink_ids):
                raise exceptions.UserError(_('There are repeated parcels.'))

    @api.constrains('partnerlink_ids', 'partnerlink_lease_ids')
    def _check_category_lease_partnerlink_ids(self):
        if len(self) == 1:
            current_file = self
            lessor_found = tenant_found = False
            if current_file.category_is_lease:
                for partnerlink in current_file.partnerlink_ids:
                    if partnerlink.is_lessor:
                        lessor_found = True
                    if partnerlink.is_tenant:
                        tenant_found = True
                if not lessor_found or not tenant_found:
                    raise exceptions.UserError(
                        _('A lessor and a tenant are required for this type '
                          'of file.'))

    @api.constrains('partnerlink_ids', 'partnerlink_trading_ids')
    def _check_category_trading_partnerlink_ids(self):
        if len(self) == 1:
            current_file = self
            seller_found = buyer_found = False
            if current_file.category_is_trading:
                for partnerlink in current_file.partnerlink_ids:
                    if partnerlink.is_seller:
                        seller_found = True
                    if partnerlink.is_buyer:
                        buyer_found = True
                if not seller_found or not buyer_found:
                    raise exceptions.UserError(
                        _('A seller and a buyer are required for this type '
                          'of file.'))


class ResFilePartnerlink(models.Model):
    _inherit = 'res.file.partnerlink'

    category_is_lease = fields.Boolean(
        string='Category is lease',
        related='file_id.category_is_lease')

    category_is_trading = fields.Boolean(
        string='Category is trading',
        related='file_id.category_is_trading')

    is_lessor = fields.Boolean(
        string='Lessor')

    is_tenant = fields.Boolean(
        string='Tenant')

    is_seller = fields.Boolean(
        string='Seller')

    is_buyer = fields.Boolean(
        string='Buyer')

    @api.onchange('is_main', 'is_lessor', 'is_tenant')
    def _onchange_lessor_tenant(self):
        for record in self:
            if record.is_lessor:
                record.is_main = False
            if record.is_tenant:
                record.is_main = True

    @api.onchange('is_main', 'is_seller', 'is_buyer')
    def _onchange_seller_buyer(self):
        for record in self:
            if record.is_seller:
                record.is_main = False
            if record.is_buyer:
                record.is_main = True


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

    category_is_lease = fields.Boolean(
        string='Category is lease',
        related='file_id.category_is_lease')

    category_is_trading = fields.Boolean(
        string='Category is trading',
        related='file_id.category_is_trading')

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
