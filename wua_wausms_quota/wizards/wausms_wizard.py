# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import requests
import json
from datetime import datetime
from jinja2 import Template, TemplateError
from lxml import etree


class WauSMSWizard(models.Model):
    _inherit = "wausms.wizard"
    _description = "Wizard to send SMS through WauSMS service"

    def _get_default_template_id(self):
        context = self._context
        default_template_id = ""
        if context.get("mode") == 'partner':
            default_template_id = self.env['ir.values'].get_default(
                'wausms.configuration', 'default_partner_template_id')
        if context.get("mode") == 'invoice':
            default_template_id = self.env['ir.values'].get_default(
                'wausms.configuration', 'default_invoice_template_id')
        if context.get("mode") == 'parcel':
            default_template_id = self.env['ir.values'].get_default(
                'wausms.configuration', 'default_parcel_template_id')
        if context.get("mode") == 'quota':
            default_template_id = self.env['ir.values'].get_default(
                'wausms.configuration', 'default_quota_template_id')
        # Detect waterconnection module
        waterconnection_module_installed = \
            self.sudo().env['ir.module.module'].search(
                [('name', '=', 'wua_wausms_waterconnection'),
                 ('state', '=', 'installed')])
        if waterconnection_module_installed:
            if context.get("mode") == 'waterconnection':
                default_template_id = self.env['ir.values'].get_default(
                    'wausms.configuration',
                    'default_waterconnection_template_id')
        return default_template_id

    # Overwrite parent field
    template_id = fields.Many2one(
        comodel_name='wausms.template',
        string='Template',
        default=_get_default_template_id,
        ondelete="set null")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        # Detect waterconnection module
        waterconnection_module_installed = \
            self.sudo().env['ir.module.module'].search(
                [('name', '=', 'wua_wausms_waterconnection'),
                 ('state', '=', 'installed')])
        context = self._context
        if context.get('mode') == 'partner':
            context_filter = "[('type', '=', 'partner')]"
        elif context.get('mode') == 'invoice':
            context_filter = "[('type', '=', 'invoice')]"
        elif context.get('mode') == 'parcel':
            context_filter = "[('type', '=', 'parcel')]"
        elif context.get('mode') == 'quota':
            context_filter = "[('type', '=', 'quota')]"
        elif waterconnection_module_installed:
            if context.get("mode") == 'waterconnection':
                context_filter = "[('type', '=', 'waterconnection')]"
        else:
            context_filter = ""
        res = super(WauSMSWizard, self).fields_view_get(
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
            'wausms.configuration', 'service_url')
        wausms_user = self.env['ir.values'].get_default(
            'wausms.configuration', 'service_user')
        sender = self.sender
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic '+self.credentials, }
        subject = self.subject

        # Reset variables
        active_ids = ""
        raw_sms_message = ""
        sms_confirmations = ""
        response_messages = ""

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
        if context.get("mode") == 'quota':
            partner_active_ids = []
            partner_quota_list = []
            quota_ids = context.get('active_ids')
            for quota_id in quota_ids:
                quota = self.env['wua.quota'].browse(quota_id)
                # Send only to partner_id of quota
                partner_quota_list.append([quota.partner_id.id, quota_id])
            # Set active_ids as list of list [[partner_id, quota_id],)
            active_ids = partner_quota_list
        if context.get("mode") == 'waterconnection':
            partner_active_ids = []
            partner_waterconnection_list = []
            waterconnection_ids = context.get('active_ids')
            for waterconnection_id in waterconnection_ids:
                waterconnection = self.env['wua.waterconnection'].browse(
                    waterconnection_id)
                # Send sms to every partner in irrigationpoint_ids
                for irrigationpoint in waterconnection.irrigationpoint_ids:
                    if irrigationpoint.partner_id:
                        item = [irrigationpoint.partner_id.id,
                                waterconnection_id]
                        if item not in partner_waterconnection_list:
                            partner_waterconnection_list.append(
                                [irrigationpoint.partner_id.id,
                                 waterconnection_id])
            # Set active_ids as list of list [[partner_id,waterconnection_id])
            active_ids = partner_waterconnection_list

        if not active_ids:
            raise ValidationError(_("There are no items selected."))

        for active_id in active_ids:
            # Set active partner,invoice and parcel (x_id is for tracking)
            if context.get("mode") == 'test':
                partner = partner_id = ""
                invoice = invoice_id = ""
                parcel = parcel_id = ""
                quota = quota_id = ""
                waterconnection = waterconnection_id = ""
            if context.get("mode") == 'partner':
                partner = self.env['res.partner'].browse(active_id)
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = parcel_id = ""
                quota = quota_id = ""
                waterconnection = waterconnection_id = ""
            if context.get("mode") == 'invoice':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = self.env['account.invoice'].browse(active_id[1])
                invoice_id = invoice.id
                parcel = parcel_id = ""
                quota = quota_id = ""
                waterconnection = waterconnection_id = ""
            if context.get("mode") == 'parcel':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = invoice_id = ""
                quota = quota_id = ""
                waterconnection = waterconnection_id = ""
                parcel = self.env['wua.parcel'].browse(active_id[1])
                parcel_id = parcel.id
            if context.get("mode") == 'quota':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = parcel_id = ""
                waterconnection = waterconnection_id = ""
                quota = self.env['wua.quota'].browse(active_id[1])
                quota_id = quota.id
            if context.get("mode") == 'waterconnection':
                partner = self.env['res.partner'].browse(active_id[0])
                partner_id = partner.id
                invoice = invoice_id = ""
                parcel = parcel_id = ""
                quota = quota_id = ""
                waterconnection = self.env['wua.waterconnection'].browse(
                    active_id[1])
                waterconnection_id = waterconnection.id

            # Set and check mobile number
            if context.get("mode") == 'test':
                phone_number = self.env['ir.values'].get_default(
                    'wausms.configuration', 'test_phone_number')
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
                        quota=quota, waterconnection=waterconnection,
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
                "text": sms_message,
                "from": sender,
                "trsec": "1"}
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

            # Get confirmations messages based in response status code
            if connection_ok:
                sms_confirmation, sms_confirmation_info = \
                    self._get_confirmation_messages(response.status_code)
                status_code = response.status_code
            else:
                sms_confirmation, sms_confirmation_info = \
                    _('ERROR: no response'), _('ERROR: no response')
                status_code = "error"

            # Add sms_confirmation message to sms_confirmations
            if not subject:
                subject = _('No subject')
            if context.get("mode") == 'test':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + "]" + '\n'
            if context.get("mode") == 'partner':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + " - " + \
                    partner.name + "]" + '\n'
            if context.get("mode") == 'invoice':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(invoice.number) + " - " + partner.name + "]" + '\n'
            if context.get("mode") == 'parcel':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(parcel.name) + " - " + partner.name + "]" + '\n'
            if context.get("mode") == 'quota':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(quota.name) + " - " + partner.name + "]" + '\n'
            if context.get("mode") == 'waterconnection':
                sms_confirmations += \
                    sms_confirmation + " -- [" + subject + " - " + \
                    str(waterconnection.name) + " - " + partner.name + "]" + \
                    '\n'

            # Response message (only shown in debug mode)
            if connection_ok:
                response_message = json.dumps(response.json(), indent=4)
                if 'error' in response.text:
                    response_message_data = json.loads(response.text)
                    response_message_data['id'] = "no-id"
                else:
                    response_message_data = json.loads(response.text)[0]
            else:
                response_message = _('ERROR: no response')
                if connection_error:
                    response_message += '\n' + connection_error
                response_message_data = {"id": "no-id", }

            # Add sms_confirmation message to sms_confirmations
            if active_id == 0:
                response_messages += "Subject: " + subject + '\n' \
                                     "Sender: " + sender + '\n' \
                                     "To: " + reformated_phone_number + '\n' \
                                     "Response: " + response_message + '\n'
            else:
                response_messages += "Subject: " + subject + '\n' \
                                     "Sender: " + sender + '\n' \
                                     "To: " + reformated_phone_number + '\n' \
                                     "Partner: " + partner.name + '\n' \
                                     "Confirmation: " + sms_confirmation_info \
                                     + '\n' \
                                     "Response: " + '\n' + response_message \
                                     + '\n'

            # Insert tracking data
            tracking_data = {
                "name": response_message_data["id"],
                "wausms_url": service_url,
                "wausms_user": wausms_user,
                "user_id": self._uid,
                "sms_time_data": datetime.today(),
                "credentials": self.credentials,
                "subject": subject,
                "partner_id": partner_id,
                "invoice_id": invoice_id,
                "parcel_id": parcel_id,
                "quota_id": quota_id,
                "waterconnection_id": waterconnection_id,
                "phone_number": reformated_phone_number,
                "sender": sender,
                "sms_message": sms_message,
                "response_code": status_code,
                "sms_confirmation": sms_confirmation,
                "sms_confirmation_info": sms_confirmation_info,
                "response_message": response_message, }
            self.env['wausms.tracking'].create(tracking_data)
            self.env.cr.commit()

        return {
            'name': _("SMS confirmation"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wausms.confirmation',
            'type': 'ir.actions.act_window',
            'context': {
                'default_response_code': '%s' % sms_confirmations,
                'default_response_message': '%s' % response_messages
                },
            'target': 'new',
            }
