# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import requests
import json
import re
from datetime import datetime
from jinja2 import Template, TemplateError
from lxml import etree


class NRSWizard(models.Model):
    _inherit = "nrs.wizard"

    def _get_default_template_id(self):
        context = self._context
        default_template_id = ""
        if context.get("mode") == 'partner':
            default_template_id = self.env['ir.values'].get_default(
                'nrs.configuration', 'default_partner_template_id')
        if context.get("mode") == 'invoice':
            default_template_id = self.env['ir.values'].get_default(
                'nrs.configuration', 'default_invoice_template_id')
        if context.get("mode") == 'parcel':
            default_template_id = self.env['ir.values'].get_default(
                'nrs.configuration', 'default_parcel_template_id')
        return default_template_id

    # Overwrite parent field
    template_id = fields.Many2one(
        comodel_name='nrs.template',
        string='Template',
        default=_get_default_template_id,
        ondelete="set null")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        context = self._context
        if context.get('mode') == 'partner':
            context_filter = "[('type', '=', 'partner')]"
        elif context.get('mode') == 'invoice':
            context_filter = "[('type', '=', 'invoice')]"
        elif context.get('mode') == 'parcel':
            context_filter = "[('type', '=', 'parcel')]"
        else:
            context_filter = ""
        res = super(NRSWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='template_id']"):
            node.set('domain', context_filter)
        res['arch'] = etree.tostring(doc)
        return res

    def _calculate_number_of_sms(self, num_char, encoding):
        if num_char == 0:
            return 0
        if encoding == 'utf-16':
            if num_char <= 70:
                return 1
            return -(-num_char // 67)
        if num_char <= 160:
            return 1
        return -(-num_char // 153)

    def _extract_encoding(self, content):
        if not isinstance(content, unicode):
            content = content.decode('utf-8')

        encoding = 'utf-16'
        gsm7_pattern = re.compile(
            ur"^[@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ "
            ur"!\"#¤%&'()*+,-./0123456789:;<=>?¡"
            ur"ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿"
            ur"abcdefghijklmnopqrstuvwxyzäöñüà]*$")

        if gsm7_pattern.match(content):
            encoding = 'gsm'
        return encoding

    @api.multi
    def send_sms_action(self, context):
        service_url = self.env['ir.values'].get_default(
            'nrs.configuration', 'service_url')
        nrs_user = self.env['ir.values'].get_default(
            'nrs.configuration', 'service_user')
        sender = self.sender
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic '+self.credentials, }
        subject = self.subject
        certify = self.certify
        sms_flash = self.sms_flash

        # Reset variables
        active_ids = ""
        raw_sms_message = ""
        sms_confirmations = ""
        response_messages = ""
        num_of_sms = 0

        # Set active_ids
        if self.wizard_mode == 'test':
            active_ids = (0,)
        if self.wizard_mode == 'partner':
            invoice_id = False
            active_ids = context.get('active_ids')
        if self.wizard_mode == 'invoice':
            partner_active_ids = []
            partner_invoice_list = []
            invoice_ids = context.get('active_ids')
            for invoice_id in invoice_ids:
                invoice = self.env['account.invoice'].browse(invoice_id)
                partner_active_ids.append(invoice.partner_id.id)
                partner_invoice_list.append([invoice.partner_id.id,
                                             invoice_id])
            # Set active_ids as list of list [[partner_id, invoice_id],)
            active_ids = partner_invoice_list
        if self.wizard_mode == 'parcel':
            partner_active_ids = []
            partner_parcel_list = []
            parcel_ids = context.get('active_ids')
            for parcel_id in parcel_ids:
                parcel = self.env['wua.parcel'].browse(parcel_id)
                # Send to all partnerlinks of parcel
                partnerlinks = parcel.partnerlink_ids
                for partnerlink in partnerlinks:
                    partner_active_ids.append(partnerlink.partner_id.id)
                    partner_parcel_list.append(
                        [partnerlink.partner_id.id, parcel_id])
            # Set active_ids as list of list [[partner_id, parcel_id],)
            active_ids = partner_parcel_list
        if not active_ids:
            raise ValidationError(_("There are no items selected."))

        for active_id in active_ids:
            # Set active partner and invoice (x_id is for tracking)
            if self.wizard_mode == 'test':
                partner = partner_id = ""
                invoice = invoice_id = ""
                parcel = parcel_id = ""
            if self.wizard_mode == 'partner':
                partner = self.env['res.partner'].browse(active_id)
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = parcel_id = ""
            if self.wizard_mode == 'invoice':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = self.env['account.invoice'].browse(active_id[1])
                invoice_id = invoice.id
                invoice_link = ""
                if self.send_invoice_link:
                    invoice_link = self._generate_invoice_link(invoice_id)
                parcel = parcel_id = ""
            if self.wizard_mode == 'parcel':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = self.env['wua.parcel'].browse(active_id[1])
                parcel_id = parcel.id
            # Set and check mobile number
            if self.wizard_mode == 'test':
                phone_number = self.env['ir.values'].get_default(
                    'nrs.configuration', 'test_phone_number')
                if not phone_number:
                    raise ValidationError(
                        _("The phone number for testing has not been set."))
            else:
                if partner.mobile:
                    phone_number = partner.mobile
                else:
                    raise ValidationError(_("Partner %s does not have a "
                                            "mobile number" % partner.name))
            reformated_phone_number = self._check_phone_number(phone_number)

            # Resolve template
            if self.sms_message:
                raw_template = Template(self.sms_message)
                try:
                    raw_sms_message = raw_template.render(
                        partner=partner, invoice=invoice, parcel=parcel,
                        datetime=datetime)
                except TemplateError as err:
                    raise ValidationError(
                        _("Error resolving template: {}".format(err.message)))
            else:
                sms_message = _('empty message')

            # Add invoice link
            if self.wizard_mode == 'invoice' and invoice_link:
                raw_sms_message += ' ' + invoice_link

            # Eliminate json special characters
            if raw_sms_message:
                sms_message = self._escape_json_special_chars(raw_sms_message)

            # Number of sms
            encoding = self._extract_encoding(sms_message)
            num_char = len(sms_message)
            number_of_sms = self._calculate_number_of_sms(num_char, encoding)

            # Check size
            if len(sms_message) > 1530:
                raise ValidationError(
                    _("Number of characters must not exceed 1530"))

            # Encode json
            data_raw = {
                "to": [reformated_phone_number],
                "from": sender,
                "message": sms_message,
                "certified": certify,
                "encoding": encoding,
                "flash": sms_flash,
                "parts": number_of_sms, }
            data = json.dumps(data_raw)

            # Send and catch response
            response = ""
            connection_error = ""
            connection_ok = False
            try:
                response = requests.post(service_url, headers=headers,
                                         data=data)
                connection_ok = True
            except requests.exceptions.RequestException as requests_error:
                connection_error = requests_error.message.message + '\n'

            # Increase counter
            num_of_sms += 1

            # Get confirmations messages based in response status code
            if connection_ok:
                sms_confirmation, sms_confirmation_info = \
                    self._get_confirmation_messages(response)
                status_code = response.status_code
            else:
                sms_confirmation, sms_confirmation_info = \
                    _('ERROR: no response'), _('ERROR: no response')
                status_code = "error"

            # Add sms_confirmation message to sms_confirmations
            if not subject:
                subject = ""
            if context.get("mode") == 'test':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    "Num " + str(number_of_sms) + " - " + \
                    sms_confirmation + " -- [" + subject + "]"
            if context.get("mode") == 'partner':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    "Num " + str(number_of_sms) + " - " + \
                    partner.name + "]"
            if context.get("mode") == 'invoice':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    "Num " + str(number_of_sms) + " - " + \
                    str(invoice.number) + " - " + partner.name + "]"
            if context.get("mode") == 'parcel':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    "Num " + str(number_of_sms) + " - " + \
                    str(parcel.name) + " - " + partner.name + "]"

            # Response message (only shown in debug mode)
            if connection_ok:
                response_message = json.dumps(response.json(), indent=4)
                if 'error' in response.text:
                    response_message_data = json.loads(response.text)
                    response_message_data = \
                        json.loads(json.dumps(response_message_data['error']))
                    name_id = "no-id"
                    certify = False
                else:
                    response_message_data = json.loads(response.text)
                    response_message_data = \
                        json.loads(json.dumps(response_message_data['result']))
                    name_id = response_message_data[0]["id"]
            else:
                response_message = _('ERROR: no response')
                certify = False
                if connection_error:
                    response_message += '\n' + connection_error
                name_id = "no-id"

            # Show if it has been certified
            is_certifed = _("No")
            if certify:
                sms_confirmations += _(" [Certified] ") + '\n'
                is_certifed = _("Yes")
            else:
                sms_confirmations += '\n'

            # Add sms_confirmation message to sms_confirmations
            if active_id == 0:
                response_messages += \
                    str(num_of_sms).zfill(4) + \
                    ' --------------------------------' + '\n' + \
                    _("Subject: ") + subject + '\n' + \
                    _("Sender: ") + sender + '\n' + \
                    _("To: ") + reformated_phone_number + '\n' + \
                    _("Certified: ") + is_certifed + '\n' + \
                    _("Number of SMS: ") + str(number_of_sms) + '\n' + \
                    _("Response: ") + response_message + '\n' + '\n'
            else:
                response_messages += \
                    str(num_of_sms).zfill(4) + \
                    ' --------------------------------' + '\n' + \
                    _("Subject: ") + subject + '\n' + \
                    _("Sender: ") + sender + '\n' + \
                    _("To: ") + reformated_phone_number + '\n' + \
                    _("Partner: ") + partner.name + '\n' + \
                    _("Confirmation: ") + sms_confirmation_info + '\n' + \
                    _("Certified: ") + is_certifed + '\n' + \
                    _("Number of SMS: ") + str(number_of_sms) + '\n' +\
                    _("Response: ") + '\n' + response_message + '\n' + '\n'

            # Insert tracking data
            tracking_data = {
                "name": name_id,
                "nrs_url": service_url,
                "nrs_user": nrs_user,
                "user_id": self._uid,
                "sms_time_data": datetime.today(),
                "credentials": self.credentials,
                "subject": subject,
                "certified": certify,
                "partner_id": partner_id,
                "invoice_id": invoice_id,
                "parcel_id": parcel_id,
                "phone_number": reformated_phone_number,
                "sender": sender,
                "sms_message": sms_message,
                "response_code": status_code,
                "sms_confirmation": sms_confirmation,
                "sms_confirmation_info": sms_confirmation_info,
                "response_message": response_message,
                "number_of_sms": number_of_sms, }
            self.env['nrs.tracking'].create(tracking_data)

        return {
            'name': _("SMS confirmation"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'nrs.confirmation',
            'type': 'ir.actions.act_window',
            'context': {
                'default_response_code': '%s' % sms_confirmations,
                'default_response_message': '%s' % response_messages
                },
            'target': 'new',
            }
