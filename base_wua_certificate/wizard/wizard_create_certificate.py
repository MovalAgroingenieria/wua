# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import models, fields, api, _


class WizardCreateCertificate(models.TransientModel):
    _name = 'wizard.create.certificate'
    _description = 'Dialog box to create a certificate'

    partner_id = fields.Many2one(
        string='Applicant',
        comodel_name='res.partner',
        required=True,
        readonly=True)

    date_of_issue = fields.Date(
        string='Date of issue',
        readonly=True)

    certificatetype_id = fields.Many2one(
        string='Certificate Type',
        comodel_name='wua.certificate.type')

    user_who_signs_id = fields.Many2one(
        string='User who signs',
        comodel_name='hr.employee')

    notes = fields.Char(
        string='Notes')

    only_parcels_as_main = fields.Boolean(
        string='Only parcels as main')

    requested_from_portal = fields.Boolean(
        string='Requested from the portal',
        readonly=True)

    can_choose_certificatetype = fields.Boolean(
        string='It is possible to choose the certificate type',
        readinly=True)

    @api.model
    def default_get(self, var_fields):
        current_partner_data = \
            self._get_current_partner_data()
        return current_partner_data

    @api.multi
    def create_certificate(self):
        self.ensure_one()
        new_certificate_id = self._create_record()
        certificate_ok = new_certificate_id != 0
        message_01_ok_wua_user = _('CERTIFICATE CREATED')
        message_01_ok_portal_user = _('REQUEST PROCESSED')
        message_02_ok_wua_user = _('(click on "See certificate" for more '
                                   'details)')
        message_02_ok_portal_user = _('(provisional certificate, the request '
                                      'will be accepted to get a valid '
                                      'certificate)')
        message_01_error = _('ERROR')
        message_02_error = _('(invalid operation)')
        message = ''
        buttons = [{'type': 'ir.actions.act_window_close',
                    'name': _('Close')}]
        if certificate_ok:
            message_01_ok = message_01_ok_wua_user
            message_02_ok = message_02_ok_wua_user
            name_of_acceptbutton = _('SEE CERTIFICATE')
            if self.requested_from_portal:
                message_01_ok = message_01_ok_portal_user
                message_02_ok = message_02_ok_portal_user
                name_of_acceptbutton = _('SEE REQUEST')
            message = '<center><b style="color:blue;">' + \
                message_01_ok + '</b><br><br>' + \
                message_02_ok + '</center>'
            id_form_view = self.env.ref(
                'base_wua_certificate.wua_certificate_display_view_form').id
            buttons.append({
                'type': 'ir.actions.act_window',
                'name': name_of_acceptbutton,
                'res_model': 'wua.certificate',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[id_form_view, 'form']],
                'res_id': new_certificate_id,
                'context': {'show_only_partner_code': True},
                'classes': 'btn-primary'})
        else:
            message = '<center><b style="color:red;">' + \
                message_01_error + '</b><br><br>' + \
                message_02_error + '</center>'
        act_window = {
            'type': 'ir.actions.act_window.message',
            'title': _('New certificate'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': buttons}
        return act_window

    def _get_current_partner_data(self):
        partner_id = self.env.context['active_id']
        date_of_issue = datetime.today().strftime('%Y-%m-%d')
        requested_from_portal = False
        if self.env.user.has_group('base_wua.group_wua_portal_user'):
            requested_from_portal = True
        certificatetype_id = None
        if requested_from_portal:
            certificatetype_id = self.env['ir.values'].get_default(
                'wua.configuration', 'portaluser_certificatetype_id')
        else:
            certificatetype_id = self.env['ir.values'].get_default(
                'wua.configuration', 'default_certificatetype_id')
        can_choose_certificatetype = True
        if requested_from_portal and certificatetype_id:
            can_choose_certificatetype = False
        user_who_signs_id = \
            self.env.user.company_id.employee_as_secretary_id.id
        only_parcels_as_main = self.env['ir.values'].get_default(
            'wua.configuration', 'only_parcels_as_main')
        return {
            'partner_id': partner_id,
            'date_of_issue': date_of_issue,
            'certificatetype_id': certificatetype_id,
            'requested_from_portal': requested_from_portal,
            'can_choose_certificatetype': can_choose_certificatetype,
            'user_who_signs_id': user_who_signs_id,
            'only_parcels_as_main': only_parcels_as_main,
            }

    def _create_record(self):
        # Certificate
        main_page = self.certificatetype_id.main_page
        final_paragraph = self.certificatetype_id.final_paragraph
        if self.partner_id.lang:
            main_page = self.with_context(
                {'lang': self.partner_id.lang}).\
                certificatetype_id.main_page
            final_paragraph = self.with_context(
                {'lang': self.partner_id.lang}).\
                certificatetype_id.final_paragraph
        fields_of_new_certificate = {
            'partner_id': self.partner_id.id,
            'certificatetype_id': self.certificatetype_id.id,
            'requested_from_portal': self.requested_from_portal,
            'user_who_signs_id': self.user_who_signs_id.id,
            'main_page': main_page,
            'final_paragraph': final_paragraph,
            }
        if self.notes:
            notes = '<p>' + self.notes + '<br></p>'
            if self.requested_from_portal:
                fields_of_new_certificate['notes_user'] = notes
            else:
                fields_of_new_certificate['notes_wua'] = notes
        new_certificate = self.env['wua.certificate'].sudo().create(
            fields_of_new_certificate)
        resp = new_certificate.id
        # Parcels of certificate
        model_partnerlinks = self.env['wua.parcel.partnerlink'].sudo()
        conditions = [('partner_id', '=', self.partner_id.id)]
        if self.only_parcels_as_main:
            conditions.append(
                ('parcel_id.partner_id', '=', self.partner_id.id))
        partnerlinks = model_partnerlinks.search(conditions)
        for partnerlink in (partnerlinks or []):
            add_parcel = \
                ((self.certificatetype_id.include_parcel_if_owner and
                 partnerlink.profile == 'O') or
                 (self.certificatetype_id.include_parcel_if_lessee and
                 partnerlink.profile == 'L') or
                 (self.certificatetype_id.include_parcel_if_payer and
                 partnerlink.profile == 'P'))
            if add_parcel:
                fields_of_new_certificateparcel = {
                    'certificate_id': new_certificate.id,
                    'parcel_id': partnerlink.parcel_id.id,
                    'cadastral_reference':
                        partnerlink.parcel_id.cadastral_reference,
                    'area_official': partnerlink.parcel_id.area_official,
                    'ownership_percentage': partnerlink.ownership_percentage,
                    'water_costs_percentage': partnerlink.water_costs_percentage,
                    'other_costs_percentage': partnerlink.other_costs_percentage,
                    'is_main': partnerlink.irrigation_partner,
                    }
                self.env['wua.certificate.parcel'].create(
                    fields_of_new_certificateparcel)
        return resp
