# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import requests
import json
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
        if context.get("mode") == 'test':
            active_ids = (0,)
        if context.get("mode") == 'partner':
            invoice_id = False
            active_ids = context.get('active_ids')
        if context.get("mode") == 'invoice':
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
        if context.get("mode") == 'parcel':
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
            if context.get("mode") == 'test':
                partner = partner_id = ""
                invoice = invoice_id = ""
                parcel = parcel_id = ""
            if context.get("mode") == 'partner':
                partner = self.env['res.partner'].browse(active_id)
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = parcel_id = ""
            if context.get("mode") == 'invoice':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = self.env['account.invoice'].browse(active_id[1])
                invoice_id = invoice.id
                parcel = parcel_id = ""
            if context.get("mode") == 'parcel':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = self.env['wua.parcel'].browse(active_id[1])
                parcel_id = parcel.id
            # Set and check mobile number
            if context.get("mode") == 'test':
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

            # Eliminate json special characters
            if raw_sms_message:
                sms_message = self._escape_json_special_chars(raw_sms_message)

            # Check size
            if len(sms_message) > 160:
                raise ValidationError(
                    _("Number of characters must not exceed 160"))

            # Encode json
            data_raw = {
                "to": [reformated_phone_number],
                "from": sender,
                "message": sms_message,
                "certified": certify,
                "flash": sms_flash}
            data = json.dumps(data_raw)

            # Send and catch response
            response = requests.post(service_url, headers=headers, data=data)

            # Increase counter
            num_of_sms += 1

            # Get confirmations messages based in response status code
            sms_confirmation, sms_confirmation_info = \
                self._get_confirmation_messages(response)

            # Add sms_confirmation message to sms_confirmations
            if not subject:
                subject = ""
            if context.get("mode") == 'test':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + "]"
            if context.get("mode") == 'partner':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    partner.name + "]"
            if context.get("mode") == 'invoice':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(invoice.number) + " - " + partner.name + "]"
            if context.get("mode") == 'parcel':
                sms_confirmations += str(num_of_sms).zfill(4) + ' -- ' + \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(parcel.name) + " - " + partner.name + "]"

            # Response message (only shown in debug mode)
            response_message = json.dumps(response.json(), indent=4)
            if 'error' in response.text:
                response_message_data = json.loads(response.text)
                response_message_data = \
                    json.loads(json.dumps(response_message_data['result']))
                response_message_data['id'] = "no-id"
                certify = False
            else:
                response_message_data = json.loads(response.text)
                response_message_data = \
                    json.loads(json.dumps(response_message_data['result']))

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
                    _("Response: ") + '\n' + response_message + '\n' + '\n'

            # Insert tracking data
            tracking_data = {
                "name": response_message_data[0]["id"],
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
                "response_code": response.status_code,
                "sms_confirmation": sms_confirmation,
                "sms_confirmation_info": sms_confirmation_info,
                "response_message": response_message}
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
