# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaCertificateType(models.Model):
    _name = 'wua.certificate.type'
    _description = 'Type of certificate'
    _order = 'certificatetype_code'

    SIZE_NAME = 50

    def _default_certificatetype_code(self):
        resp = 0
        certificatetypes = self.search([], limit=1,
                                       order='certificatetype_code desc')
        if certificatetypes:
            resp = certificatetypes[0].certificatetype_code + 1
        else:
            resp = 1
        return resp

    certificatetype_code = fields.Integer(
        string='Code',
        default=_default_certificatetype_code,
        required=True,
        index=True)

    name = fields.Char(
        string='Name',
        size=SIZE_NAME,
        required=True,
        translate=True,
        index=True)

    is_standard_certificatetype = fields.Boolean(
        string='WUA Master Certificate Type',
        default=False)

    certificate_ids = fields.One2many(
        string='Certificates',
        comodel_name='wua.certificate',
        inverse_name='certificatetype_id')

    number_of_certificates = fields.Integer(
        string='Number of certificates',
        compute_sudo=True,
        compute='_compute_number_of_certificates')

    mailtemplate_id = fields.Many2one(
        string='Email Template',
        comodel_name='mail.template')

    iractreportxml_id = fields.Many2one(
        string='Report',
        comodel_name='ir.actions.report.xml',
        domain=[('model', '=', 'wua.certificate'),
                ('report_type', '=', 'qweb-pdf')],
        help='Report to use for this type of certificate (optional); '
             'if not indicated, the standard certificate report will be used')

    notes = fields.Html(
        string='Notes',
        translate=True)

    notes_text = fields.Char(
        string="Notes (as text)",
        compute='_compute_notes_text')

    main_page = fields.Html(
        string='Certificate Template',
        translate=True)

    final_paragraph = fields.Html(
        string='Final Paragraph',
        translate=True)

    include_parcel_if_owner = fields.Boolean(
        string='Include parcel if partner is owner',
        help='When creating a certificate, include parcel if partner '
             'is owner (or co-owner)',
        default=True)

    include_parcel_if_lessee = fields.Boolean(
        string='Include parcel if partner is lessee',
        help='When creating a certificate, include parcel if partner '
             'is lessee',
        default=True)

    include_parcel_if_payer = fields.Boolean(
        string='Include parcel if partner is payer',
        help='When creating a certificate, include parcel if partner '
             'is payer',
        default=True)

    parcel_img_coordinate_grid = fields.Boolean(
        string='Include coordinate GRID in aerial images of parcel',
        default=False)

    report_in_official_units = fields.Boolean(
        string='Report in official units',
        help='When creating a certificate, show the values in the '
             'official units (ha)',
        default=False)

    map_type_in_report = fields.Selection(
        selection=[
            ('00_none', 'No map'),
            ('01_one', '1 map per page'),
            ('02_four', '4 maps per page')],
        string='Map type in report',
        default='00_none',
        help="Determines the number of aerial images per page.")

    _sql_constraints = [
        ('valid_certificatetype_code', 'CHECK (certificatetype_code > 0)',
         'The certificate type code must be a positive value.'),
        ('unique_certificatetype_code', 'UNIQUE (certificatetype_code)',
         'Existing certificate type.'),
        ]

    @api.multi
    def _compute_number_of_certificates(self):
        for record in self:
            number_of_certificates = 0
            if record.certificate_ids:
                number_of_certificates = len(record.certificate_ids)
            record.number_of_certificates = number_of_certificates

    @api.multi
    def _compute_notes_text(self):
        model_converter = self.env["ir.fields.converter"]
        for record in self:
            notes_text = ''
            if record.notes:
                notes_text = model_converter.text_from_html(
                    record.notes, 50, 150)
            record.notes_text = notes_text

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            display_name = record.name + \
                ' [' + str(record.certificatetype_code) + ']'
            result.append((record.id, display_name))
        return result

    @api.multi
    def write(self, vals):
        user_is_certificate_manager_only = \
            (self.env.user.has_group(
                'base_wua_certificate.group_wua_certificate_manager') and
             (not self.env.user.has_group(
                 'base_wua.group_wua_manager')))
        for record in self:
            if (user_is_certificate_manager_only and
               (record.create_uid != self.env.user)):
                raise exceptions.UserError(_(
                    'A certificate manger can only edit their own '
                    'certificate types.'))
        return super(WuaCertificateType, self).write(vals)

    @api.multi
    def unlink(self):
        user_is_certificate_manager_only = \
            (self.env.user.has_group(
                'base_wua_certificate.group_wua_certificate_manager') and
             (not self.env.user.has_group(
                 'base_wua.group_wua_manager')))
        for record in self:
            if record.is_standard_certificatetype:
                raise exceptions.UserError(_('It is not possible to remove '
                                             'the \'STANDARD\' certificate '
                                             'type.'))
            if (user_is_certificate_manager_only and
               (record.create_uid != self.env.user)):
                raise exceptions.UserError(_(
                    'A certificate manger can only delete their own '
                    'certificate types.'))
        res = super(WuaCertificateType, self).unlink()
        return res

    @api.multi
    def action_get_certificates(self):
        self.ensure_one()
        if self.certificate_ids:
            id_tree_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_display_view_form').id
            search_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Certificates'),
                'res_model': 'wua.certificate',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.certificate_ids.ids)],
                }
            return act_window
    @api.model
    def _compute_area_measurement_name(self, official_area):

        area__measurement_type = official_area
        results = ""
        if area__measurement_type:
            if area__measurement_type == 0:
                results = _('ha')
            else:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                if area_measurement_name:
                    results = area_measurement_name.decode('utf_8')
                else:
                    results = ""
        else:
            results = _('ha')
        return results