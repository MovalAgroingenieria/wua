# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import zipfile
import base64
from lxml import etree
from jinja2 import Template, TemplateError
from datetime import date
from babel import dates
from base64 import encodestring
from os import remove
from logging import getLogger
from odoo import models, fields, api, exceptions, _
from odoo.tools import config


class WuaCertificate(models.Model):
    _name = 'wua.certificate'
    _description = 'Certificate'
    _inherit = 'mail.thread'
    _order = 'name desc'

    SIZE_NAME = 20

    def _default_certificatetype_id(self):
        resp = 0
        default_certificatetype_id = self.env['ir.values'].get_default(
            'wua.configuration', 'default_certificatetype_id')
        if default_certificatetype_id:
            resp = default_certificatetype_id
        return resp

    def _default_requested_from_portal(self):
        resp = False
        user = self.env.user
        if user.has_group('base_wua.group_wua_portal_user'):
            resp = True
        return resp

    name = fields.Char(
        string='Reference',
        size=SIZE_NAME,
        readonly=True,
        required=True,
        index=True)

    reference_number = fields.Char(
        string='Reference Number',
        compute='_compute_reference_number',
        search='_search_reference_number')

    date_of_issue = fields.Date(
        string='Date of issue',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    partner_id = fields.Many2one(
        string='Applicant',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict')

    partner_code = fields.Char(
        string='Applicant (code)',
        store=True,
        compute='_compute_partner_code')

    certificatetype_id = fields.Many2one(
        string='Certificate Type',
        comodel_name='wua.certificate.type',
        default=_default_certificatetype_id,
        required=True,
        ondelete='restrict')

    main_page = fields.Html(
        string='Main Page')

    final_paragraph = fields.Html(
        string='Final Paragraph',
        translate=True)

    certificateparcel_ids = fields.One2many(
        string='Associated Parcels',
        comodel_name='wua.certificate.parcel',
        inverse_name='certificate_id')

    state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_validated', 'Validated'),
            ('03_sent', 'Sent'),
        ],
        string='State',
        default='01_draft',
        index=True,
        track_visibility='onchange')

    requested_from_portal = fields.Boolean(
        string='Requested from the portal',
        default=_default_requested_from_portal)

    current_user_id = fields.Many2one(
        string='Current User',
        comodel_name='res.users',
        compute='_compute_current_user_id')

    user_who_validates_id = fields.Many2one(
        string='User who validates',
        comodel_name='res.users',
        ondelete='restrict')

    user_who_signs_id = fields.Many2one(
        string='User who signs',
        comodel_name='hr.employee',
        default=lambda self: self.env.user.company_id.employee_as_secretary_id,
        ondelete='restrict')

    name_of_signer = fields.Char(
        string='Name of signer',
        compute='_compute_name_of_signer')

    notes_wua = fields.Html(
        string='Notes WUA')

    notes_user = fields.Html(
        string='Notes User')

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        index=True,
        compute='_compute_number_of_parcels')

    total_area_official = fields.Float(
        string='Total Area',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_total_area_official')

    document = fields.Binary(
        string='Certificate (PDF)',
        attachment=True)

    document_name = fields.Char(
        string='Document Name')

    image = fields.Binary(
        string='Image',
        compute='_compute_image')

    partner_name = fields.Char(
        string='Partner Name',
        related='partner_id.name')

    html_certificate_title = fields.Html(
        string='Certificate Title',
        compute='_compute_html_certificate_title')

    rendered_main_page = fields.Html(
        string='Preview of certificate',
        compute='_compute_rendered_main_page')

    rendered_final_paragraph = fields.Html(
        string='Preview of certificate (final paragraph)',
        compute='_compute_rendered_final_paragraph')

    has_mailtemplate = fields.Boolean(
        string='With mail template',
        compute='_compute_has_mailtemplate')

    map_type_in_report = fields.Selection(
        string='Map type in report',
        related='certificatetype_id.map_type_in_report')

    parcel_img_coordinate_grid = fields.Boolean(
        string='Include coordinate GRID in aerial images of parcel',
        related='certificatetype_id.parcel_img_coordinate_grid')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing reference number.'),
        ]

    @api.multi
    def _compute_reference_number(self):
        for record in self:
            record.reference_number = \
                self._get_reference_number_from_code(record.name)

    @api.multi
    def _compute_image(self):
        for record in self:
            image = None
            if record.partner_id:
                image = record.partner_id.image_medium
            record.image = image

    @api.depends('partner_id', 'partner_id.partner_code')
    def _compute_partner_code(self):
        for record in self:
            partner_code = ''
            if record.partner_id:
                partner_code = record.partner_id.partner_code
            record.partner_code = partner_code

    @api.multi
    def _compute_current_user_id(self):
        for record in self:
            current_user_id = None
            if self.env.user:
                current_user_id = self.env.user
            record.current_user_id = current_user_id

    @api.multi
    def _compute_name_of_signer(self):
        for record in self:
            name_of_signer = ''
            if record.user_who_signs_id:
                name_of_signer = record.user_who_signs_id.name
                if (record.user_who_signs_id.user_id and
                   record.user_who_signs_id.user_id.firstname):
                    signer = record.user_who_signs_id.user_id
                    name_of_signer = signer.firstname.strip()
                    if (signer.lastname):
                        name_of_signer = (name_of_signer + ' ' +
                                          signer.lastname).strip()
                    if (signer.lastname2):
                        name_of_signer = (name_of_signer + ' ' +
                                          signer.lastname2).strip()
            record.name_of_signer = name_of_signer

    @api.depends('certificateparcel_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = 0
            if record.certificateparcel_ids:
                number_of_parcels = len(record.certificateparcel_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('certificateparcel_ids')
    def _compute_total_area_official(self):
        for record in self:
            total_area_official = 0
            if record.certificateparcel_ids:
                total_area_official = sum(map(lambda x: x.area_official,
                                              record.certificateparcel_ids))
            record.total_area_official = total_area_official

    @api.multi
    def _compute_html_certificate_title(self):
        try:
            settings = self.env['res.backend.settings'].search([])
            report_color = str(settings[0].report_motive_color)
        except Exception:
            report_color = '#696969'
        for record in self:
            html_certificate_title = ''
            if record.name:
                label_title = _('C E R T I F I C A T E')
                header = '<div class="text-center"><b>' + label_title + \
                         '</b></div>'
                body = '<div class="text-center"><h1>' + \
                    record.reference_number + '</h1></div>'
                html_certificate_title = \
                    '<div class="panel-body text-left" ' + \
                    'style="background:#f4f6f6;' + \
                    'border-color: ' + report_color + '; border-width:1px;' + \
                    'border-style:solid;padding-top:8px;' + \
                    'padding-bottom:8px;' + \
                    'margin-left:0px;margin-right:0px">' + \
                    header + body + '</div>'
            record.html_certificate_title = html_certificate_title

    @api.multi
    def _compute_rendered_main_page(self):
        for record in self:
            rendered_main_page = ''
            if record.main_page:
                rendered_main_page = \
                    record._get_rendered_text()
            record.rendered_main_page = rendered_main_page

    @api.multi
    def _compute_rendered_final_paragraph(self):
        for record in self:
            rendered_final_paragraph = ''
            if record.final_paragraph:
                rendered_final_paragraph = \
                    record._get_rendered_text(is_main_page=False)
            record.rendered_final_paragraph = rendered_final_paragraph

    @api.multi
    def _compute_has_mailtemplate(self):
        for record in self:
            has_mailtemplate = False
            if (record.certificatetype_id and
               record.certificatetype_id.mailtemplate_id):
                has_mailtemplate = True
            record.has_mailtemplate = has_mailtemplate

    @api.model
    def _search_reference_number(self, operator, value):
        if operator == 'ilike':
            certificate_ids = []
            sequence_certificate_code_id = self.env['ir.values'].get_default(
                'wua.configuration', 'sequence_certificate_code_id')
            if sequence_certificate_code_id:
                sequence_certificate_code = self.env['ir.sequence'].browse(
                    sequence_certificate_code_id)
                if (sequence_certificate_code and
                   sequence_certificate_code.prefix and
                   sequence_certificate_code.padding):
                    limit_for_numeric_suffix = \
                        sequence_certificate_code.prefix[-1]
                    pos_for_numeric_suffix_in_value = \
                        value.find(limit_for_numeric_suffix)
                    if (pos_for_numeric_suffix_in_value != -1 and
                       len(value) > pos_for_numeric_suffix_in_value + 1):
                        len_suffix = \
                            len(value) - pos_for_numeric_suffix_in_value - 1
                        if len_suffix > 0:
                            suffix = value[-len_suffix:]
                            padding = sequence_certificate_code.padding
                            if len(suffix) < padding:
                                suffix = \
                                    suffix.zfill(padding)
                                prefix = \
                                    value[:pos_for_numeric_suffix_in_value + 1]
                                value = prefix + suffix
            certificates = self.search([('name', 'ilike', value)])
            if certificates:
                certificate_ids = certificates.ids
            return ([('id', 'in', certificate_ids)])

    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            if (not record.partner_id.is_wua_partner):
                raise exceptions.UserError(
                    _('The partner must be a WUA user.'))

    @api.onchange('certificatetype_id')
    def _onchange_certificatetype_id(self):
        self.main_page = self.certificatetype_id.main_page
        self.final_paragraph = self.certificatetype_id.final_paragraph

    @api.model
    def create(self, vals):
        (certificate_ok, error_message) = self._is_possible_create(vals)
        if not certificate_ok:
            raise exceptions.UserError(error_message)
        model_ir_sequence = self.env['ir.sequence'].sudo()
        sequence_certificate_code = None
        sequence_certificate_code_id = self.env['ir.values'].get_default(
            'wua.configuration', 'sequence_certificate_code_id')
        if sequence_certificate_code_id:
            sequence_certificate_code = \
                model_ir_sequence.browse(sequence_certificate_code_id)
        if sequence_certificate_code:
            vals['name'] = model_ir_sequence.next_by_code(
                sequence_certificate_code.code)
        new_certificate = super(WuaCertificate, self).create(vals)
        if new_certificate.user_who_signs_id:
            self._send_message_to_signer(new_certificate)
        return new_certificate

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaCertificate, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_area = ' (' + area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='total_area_official']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_certificate',
                        self.__class__.total_area_official.string)
                node.set('string', original_label + suffix_area)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def write(self, vals):
        for record in self:
            (certificate_ok, error_message) = record._is_possible_write(vals)
            if not certificate_ok:
                raise exceptions.UserError(error_message)
        super(WuaCertificate, self).write(vals)
        return True

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            display_name = \
                self._get_reference_number_from_code(record.name)
            result.append((record.id, display_name))
        return result

    def _get_reference_number_from_code(self, code):
        resp = code
        if code:
            pos_slash = code.find('/')
            if pos_slash > 0:
                suffix = code[pos_slash+1:]
                if suffix:
                    suffix = suffix.lstrip('0')
                    resp = code[:pos_slash + 1] + suffix
        return resp

    def _is_possible_create(self, vals):
        certificate_ok = True
        error_message = ''
        allowed_request_for_portal_user = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'allowed_request_for_portal_user')
        if not allowed_request_for_portal_user:
            if self.env.user.has_group('base_wua.group_wua_portal_user'):
                certificate_ok = False
                error_message = _('It is not allowed to create certificates '
                                  'from the electronic office.')
        return (certificate_ok, error_message)

    def _is_possible_write(self, vals):
        certificate_ok = True
        error_message = ''
        allowed_request_for_portal_user = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'allowed_request_for_portal_user')
        if not allowed_request_for_portal_user:
            if self.env.user.has_group('base_wua.group_wua_portal_user'):
                certificate_ok = False
                error_message = _('It is not allowed to modify certificates '
                                  'from the electronic office.')
        return (certificate_ok, error_message)

    def _send_message_to_signer(self, new_certificate):
        lang = None
        if new_certificate.sudo().user_who_signs_id.user_id:
            lang = new_certificate.sudo().user_who_signs_id.user_id.lang
        message_to_signer_prefix = _('New certificate. Reference:')
        message_to_signer_warning = _('(requested from electronic office)')
        message_to_signer_partner = _('Applicant:')
        if lang:
            message_to_signer_prefix = self._get_value_from_translation(
                'base_wua_certificate', 'New certificate. Reference:', lang)
            message_to_signer_warning = self._get_value_from_translation(
                'base_wua_certificate', '(requested from electronic office)',
                lang)
            message_to_signer_partner = self._get_value_from_translation(
                'base_wua_certificate', 'Applicant:', lang)
        message = message_to_signer_prefix + ' ' + \
            new_certificate.reference_number
        if new_certificate.requested_from_portal:
            message = message + ' ' + message_to_signer_warning
        message = message + '. ' + message_to_signer_partner + ' ' + \
            new_certificate.partner_id.name
        new_certificate.sudo().user_who_signs_id.message_post(message)

    def _get_value_from_translation(self, module, src, lang=None):
        resp = src
        if not lang:
            lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp

    def _get_rendered_text(self, is_main_page=True):
        resp = ''
        lang = self.partner_id.lang
        if not lang:
            lang = 'en_US'
        today = date.today()
        try:
            if is_main_page:
                template = Template(self.main_page)
            else:
                template = Template(self.final_paragraph)
            resp = template.render(
                partner=self.partner_id,
                certificate=self,
                current_day=dates.format_date(today, 'd', locale=lang),
                current_month=dates.format_date(today, 'LLLL', locale=lang),
                current_year=dates.format_date(today, 'y', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    @api.multi
    def action_preview_certificate(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Preview the certificate'),
            'res_model': 'wizard.preview.certificate',
            'src_model': 'wua.certificate',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    @api.multi
    def action_validate_certificate(self):
        self.ensure_one()
        self.state = '02_validated'
        report_name = 'base_wua_certificate.report_wua_certificate'
        if self.certificatetype_id.iractreportxml_id:
            report_name = self.certificatetype_id.iractreportxml_id.report_name
        pdf = self.env['report'].with_context(
            {'lang': self.partner_id.lang}).get_pdf(
                [self.id], report_name)
        if pdf:
            self.write({
                'user_who_validates_id': self.env.user.id,
                'document': encodestring(pdf),
                'document_name': self.name + '.pdf'
                })
        if self.env['ir.values'].get_default(
                'wua.configuration', 'with_letter'):
            self._create_letters()

    @api.multi
    def action_print_certificate(self):
        self.ensure_one()
        report_name = 'base_wua_certificate.report_wua_certificate'
        if self.certificatetype_id.iractreportxml_id:
            report_name = self.certificatetype_id.iractreportxml_id.report_name
        return self.env['report'].with_context(
            {'lang': self.partner_id.lang}).get_action(
                self, report_name)

    @api.multi
    def action_send_certificate(self):
        self.ensure_one()
        mail_ok = self._send_mail()
        if not mail_ok:
            raise exceptions.UserError(
                _('ATTENTION: The mail could not be sent.'))
        self.state = '03_sent'

    @api.multi
    def action_cancel_certificate(self):
        self.ensure_one()
        self._delete_attachment()
        self.write({
            'state': '01_draft',
            'user_who_validates_id': None,
            'document': None,
            'document_name': None
            })

    @api.multi
    def action_generate_parcel_shp(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        zip_buffer = io.BytesIO()
        result = ''
        filename = ''
        # More than one certificate (Tree view multiple selection)
        if (len(self) > 1):
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_STORED, False) \
                    as zip_file:
                for record in self:
                    parcels_of_certificate = record.certificateparcel_ids.\
                        filtered(lambda x: x.included_in_certificate).mapped(
                            lambda x: x.parcel_id)
                    result = parcels_of_certificate.generate_parcel_shp(
                        record.partner_id, True)
                    zip_file.writestr(
                        record.name.replace('/', '-') + '.zip',
                        base64.b64decode(result))
            result = base64.b64encode(zip_buffer.getvalue())
            certificates_label = _('Certificates')
            filename = certificates_label + '.zip'
        # Just one certificate (Form or tree view with one selected)
        else:
            parcels_of_certificate = self.certificateparcel_ids.filtered(
                lambda x: x.included_in_certificate).mapped(
                lambda x: x.parcel_id)
            result = parcels_of_certificate.generate_parcel_shp(
                self.partner_id, True)
            filename = self.name.replace('/', '-') + '.zip'
        attachment_obj = self.sudo().env['ir.attachment']
        # Attachment info to create
        attachment_info = {
            'name': 'certificates_shp_download',
            'datas_fname': filename,
            'datas': result,
            'res_model': 'wua.certificate'
        }
        # Info of the attachment that will be deleted
        attachment_to_delete_domain = [
            ('name', '=', 'certificates_shp_download'),
            ('res_model', '=', 'wua.certificate')]
        if (self.env.user and self.env.user.is_wua_portal_user):
            attachment_to_delete_domain.append(
                ('res_model', '=', 'res.partner'))
            attachment_to_delete_domain.append(
                ('res_id', '=', self.env.user.partner_id.id))
            attachment_info.update({
                'res_model': 'res.partner',
                'res_id': self.env.user.partner_id.id
            })
            # Removed older shp
        attachment_obj.search(attachment_to_delete_domain).unlink()
        # create attachment, add timestamp or something here?
        attachment_id = attachment_obj.create(attachment_info)
        # prepare download url
        download_url = '/web/content/' + str(attachment_id.id) + \
            '?download=true'
        # download, should remove after?
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    @api.multi
    def _delete_attachment(self):
        base_path = config.filestore(self._cr.dbname)
        if base_path and len(base_path) >= 1:
            if base_path[-1:] != '/':
                base_path = base_path + '/'
        if base_path:
            for record in self:
                self.env.cr.execute(
                    """
                    SELECT store_fname FROM ir_attachment
                    WHERE res_model='wua.certificate' AND res_id=
                    """ + str(record.id))
                query_results = self.env.cr.dictfetchall()
                for row in (query_results or []):
                    attachment_to_delete = base_path + row.get('store_fname')
                    try:
                        remove(attachment_to_delete)
                    except Exception:
                        pass

    @api.multi
    def _send_mail(self):
        resp = True
        _logger = getLogger(self.__class__.__name__)
        for record in self:
            certificate = record
            if (certificate.state == '02_validated' and
               certificate.has_mailtemplate):
                preffix_message = _('Mail with certificate') + ' ' + \
                    certificate.reference_number + ', ' + \
                    _('for the partner') + ' \"' + certificate.partner_name + \
                    '\": '
                suffix_message = _('sent successfully')
                send_ok = True
                try:
                    mailtemplate = \
                        certificate.certificatetype_id.mailtemplate_id
                    mailtemplate.send_mail(certificate.id, force_send=True)
                except Exception:
                    send_ok = False
                if not send_ok:
                    resp = False
                    suffix_message = _('send error')
                _logger.info(preffix_message + suffix_message)
        return resp

    @api.multi
    def action_exclude_all_parcels(self):
        for record in self:
            if (len(record.certificateparcel_ids) > 0):
                record.certificateparcel_ids.write({
                    'included_in_certificate': False,
                })

    @api.multi
    def action_include_all_parcels(self):
        for record in self:
            if (len(record.certificateparcel_ids) > 0):
                record.certificateparcel_ids.write({
                    'included_in_certificate': True,
                })

    # Auxiliar method to be inherit and extended
    def _get_fields_of_new_certificate(self, new_certificate, partnerlink):
        return {
            'certificate_id': new_certificate.id,
            'parcel_id': partnerlink.parcel_id.id,
            'area_intersected_perimeter':
                partnerlink.parcel_id.area_intersected_perimeter,
            'area_gis':
                partnerlink.parcel_id.area_gis,
            'cadastral_reference':
                partnerlink.parcel_id.cadastral_reference,
            'area_official': partnerlink.parcel_id.area_official,
            'ownership_percentage': partnerlink.ownership_percentage,
            'water_costs_percentage':
                partnerlink.water_costs_percentage,
            'other_costs_percentage':
                partnerlink.other_costs_percentage,
            'is_main': partnerlink.irrigation_partner,
        }

    @api.model
    def get_validated_certificate(self, identification, cert_type=1,
                                  is_portal_user=True, pdf_file=''):
        resp = False
        # Initial control.
        partner_code = 0
        vat = ''
        if identification.isdigit():
            partner_code = identification
        else:
            vat = identification
        if not cert_type:
            cert_type = 1
        # Get the partner and the certificate type.
        if not partner_code and not vat:
            return False
        if vat:
            if len(vat) > 2:
                if (vat[0:1].isdigit() or vat[1:2].isdigit()):
                    vat = 'ES' + vat
            else:
                return False
        model_res_partner = self.env['res.partner']
        model_certificate_type = self.env['wua.certificate.type']
        model_wua_certificate = self.env['wua.certificate'].sudo()
        model_partnerlinks = self.env['wua.parcel.partnerlink'].sudo()
        model_wua_certificate_parcel = self.env['wua.certificate.parcel']
        model_report = self.env['report']
        certificatetype = model_certificate_type.search(
            [('certificatetype_code', '=', cert_type)])
        if certificatetype:
            certificatetype = certificatetype[0]
        partner = None
        if partner_code:
            partner = model_res_partner.search(
                [('partner_code', '=', partner_code)])
        else:
            partner = model_res_partner.search(
                [('vat', '=', vat), ('is_wua_partner', '=', True)])
        if partner:
            partner = partner[0]
        if (not partner or not certificatetype):
            return False
        # Create the certificate.
        main_page = certificatetype.with_context(
            {'lang': partner.lang}).main_page
        final_paragraph = certificatetype.with_context(
            {'lang': partner.lang}).final_paragraph
        fields_of_new_certificate = {
            'partner_id': partner.id,
            'certificatetype_id': certificatetype.id,
            'requested_from_portal': is_portal_user,
            'main_page': main_page,
            'final_paragraph': final_paragraph,
            }
        user_who_signs = self.env.user.company_id.employee_as_secretary_id
        if user_who_signs:
            user_who_signs_id = user_who_signs.id
            fields_of_new_certificate.update(
                {'user_who_signs_id': user_who_signs_id})
        new_certificate = model_wua_certificate.create(
            fields_of_new_certificate)
        partnerlinks = model_partnerlinks.search(
            [('partner_id', '=', partner.id)])
        for partnerlink in (partnerlinks or []):
            add_parcel = \
                ((certificatetype.include_parcel_if_owner and
                 partnerlink.profile == 'O') or
                 (certificatetype.include_parcel_if_lessee and
                 partnerlink.profile == 'L') or
                 (certificatetype.include_parcel_if_payer and
                 partnerlink.profile == 'P'))
            if add_parcel:
                fields_of_new_certificateparcel = self.\
                    _get_fields_of_new_certificate(
                        new_certificate, partnerlink)
                model_wua_certificate_parcel.create(
                    fields_of_new_certificateparcel)
        # Get the PDF.
        if self._allowed_signature(new_certificate):
            new_certificate.state = '02_validated'
            report_name = 'base_wua_certificate.report_wua_certificate'
            if certificatetype.iractreportxml_id:
                report_name = certificatetype.iractreportxml_id.report_name
            pdf = model_report.with_context(
                {'lang': partner.lang}).get_pdf(
                    [new_certificate.id], report_name)
            if pdf:
                resp = pdf
                new_certificate.write({
                    'user_who_validates_id': self.env.user.id,
                    'document': encodestring(pdf),
                    'document_name': new_certificate.name + '.pdf'
                    })
                if pdf_file:
                    try:
                        f = open(pdf_file, 'wb')
                        f.write(pdf)
                        f.close()
                    except Exception:
                        pass
        return resp

    @api.multi
    def _create_letters(self):
        model_res_letter = self.env['res.letter']
        for record in self:
            values = {
                'name': record.name + ' (' +
                record.certificatetype_id.name + ')',
                'move': 'out',
                'state': 'draft',
                'recipient_partner_id': record.partner_id.id,
            }
            model_res_letter.create(values)

    # Hook
    def _allowed_signature(self, certificate):
        return True


class WuaCertificateParcel(models.Model):
    _name = 'wua.certificate.parcel'
    _description = 'Parcel of a certificate'
    _order = 'name'

    SIZE_NAME = 41
    SIZE_CADASTRAL_REFERENCE = 14

    certificate_id = fields.Many2one(
        string='Certificate',
        comodel_name='wua.certificate',
        required=True,
        index=True,
        ondelete='cascade')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='restrict')

    name = fields.Char(
        string='Certificate Parcel',
        size=SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=SIZE_CADASTRAL_REFERENCE)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    area_official_hec = fields.Float(
        string='Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec')

    area_intersected_perimeter = fields.Float(
        string='Area intersected with the perimeter',
        digits=(32, 4),
        default=0)

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        default=0)

    ownership_percentage = fields.Float(
        string='Ownership %',
        digits=(5, 2),
        default=0)

    water_costs_percentage = fields.Float(
        string='Water Costs %',
        digits=(5, 2),
        default=0)

    other_costs_percentage = fields.Float(
        string='Other Costs %',
        digits=(5, 2),
        default=0)

    is_main = fields.Boolean(
        string='Main',
        default=False)

    included_in_certificate = fields.Boolean(
        string='Included',
        default=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Certificate-Parcel.'),
        ]

    @api.depends('certificate_id', 'certificate_id.name',
                 'parcel_id', 'parcel_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.certificate_id and record.parcel_id and
               record.certificate_id.name and record.parcel_id.name):
                name = record.certificate_id.name + '-' + record.parcel_id.name
            record.name = name

    @api.depends('area_official')
    def _compute_area_official_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = \
                self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        for record in self:
            record.area_official_hec = factor * record.area_official

    @api.onchange('parcel_id')
    def _onchange_parcel_id(self):
        (cadastral_reference, area_official, ownership_percentage,
         water_costs_percentage, other_costs_percentage,
         area_intersected_perimeter, area_gis) = \
            self._get_partnerlink_data(self.certificate_id.partner_id,
                                       self.parcel_id)
        self.cadastral_reference = cadastral_reference
        self.area_official = area_official
        self.ownership_percentage = ownership_percentage
        self.water_costs_percentage = water_costs_percentage
        self.other_costs_percentage = other_costs_percentage
        self.area_intersected_perimeter = area_intersected_perimeter
        self.area_gis = area_gis

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaCertificateParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            intersection_management = self.env['ir.values'].get_default(
                'wua.configuration', 'intersection_management')
            use_intersected_area = self.env['ir.values'].get_default(
                'wua.configuration', 'use_intersected_area')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_area = ' (' + area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = \
                    self.env['wua.certificate']._get_value_from_translation(
                        'base_wua_certificate',
                        self.__class__.area_official.string)
                node.set('string', original_label + suffix_area)
            for node in doc.xpath("//field[@name='area_gis']"):
                original_label = \
                    self.env['wua.certificate']._get_value_from_translation(
                        'base_wua_certificate',
                        self.__class__.area_gis.string)
                node.set('string', original_label + suffix_area)
            for node in doc.xpath("//field[@name='area_intersected_"
                                  "perimeter']"):
                original_label = \
                    self.env['wua.certificate']._get_value_from_translation(
                        'base_wua_certificate',
                        self.__class__.area_intersected_perimeter.string)
                node.set('string', original_label + suffix_area)
                if (not use_intersected_area or not intersection_management):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            res['arch'] = etree.tostring(doc)
        return res

    def _get_partnerlink_data(self, partner, parcel):
        cadastral_reference = ''
        area_official = 0
        ownership_percentage = 0
        water_costs_percentage = 0
        other_costs_percentage = 0
        area_intersected_perimeter = 0
        area_gis = 0
        if partner and parcel:
            partnerlinks = self.env['wua.parcel.partnerlink'].search(
                [('partner_id', '=', partner.id),
                 ('parcel_id', '=', parcel.id)])
            if partnerlinks:
                cadastral_reference = parcel.cadastral_reference
                area_official = parcel.area_official
                area_intersected_perimeter = parcel.area_intersected_perimeter
                area_gis = parcel.area_gis
                partnerlink_data = partnerlinks[0]
                ownership_percentage = \
                    partnerlink_data.ownership_percentage
                water_costs_percentage = \
                    partnerlink_data.water_costs_percentage
                other_costs_percentage = \
                    partnerlink_data.other_costs_percentage
        return (cadastral_reference, area_official, ownership_percentage,
                water_costs_percentage, other_costs_percentage,
                area_intersected_perimeter, area_gis)

