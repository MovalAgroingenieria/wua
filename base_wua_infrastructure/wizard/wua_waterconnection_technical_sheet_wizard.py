# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WuaWaterconnectionTechnicalSheetWizard(models.TransientModel):
    _name = 'wua.waterconnection.technical.sheet.wizard'
    _description = 'Wizard to send the technical sheet report by e-mail'

    template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Email Template',
        domain="[('model', '=', 'wua.waterconnection')]",
        required=True,
    )
    subject = fields.Char(
        string='Subject',
        required=True,
    )
    body = fields.Html(
        string='Message Body',
    )

    @api.model
    def _get_payer_partners(self, wc):
        """Return payer partner recordset for a single waterconnection *wc*.

        Looks for a partner with profile 'P' (payer) among the
        partnerlinks of the connected parcels.  When no payer profile
        is found, falls back to the first partner found.
        This method can be overridden by other modules to change the
        recipient selection logic.
        """
        payer_partner = None
        first_partner = None
        for ip in wc.irrigationpoint_ids:
            parcel = ip.parcel_id
            if not parcel:
                continue
            for link in parcel.partnerlink_ids:
                if not link.partner_id:
                    continue
                if first_partner is None:
                    first_partner = link.partner_id
                if link.profile == 'P' and payer_partner is None:
                    payer_partner = link.partner_id
        if payer_partner:
            return payer_partner
        if first_partner:
            return first_partner
        return self.env['res.partner']

    @api.model
    def default_get(self, fields_list):
        res = super(WuaWaterconnectionTechnicalSheetWizard, self).default_get(
            fields_list)
        # Load default template
        template = self.env.ref(
            'base_wua_infrastructure'
            '.email_template_waterconnection_technical_sheet',
            raise_if_not_found=False,
        )
        if template:
            res['template_id'] = template.id
            res['subject'] = template.subject or ''
            res['body'] = template.body_html or ''
        return res

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if not self.template_id:
            return
        self.subject = self.template_id.subject or ''
        self.body = self.template_id.body_html or ''

    @api.multi
    def action_send(self):
        self.ensure_one()
        template = self.template_id
        if not template:
            raise UserError(
                _('No email template selected. Please choose one before '
                  'sending.'))
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_id = self._context.get('active_id')
            if active_id:
                active_ids = [active_id]
        if not active_ids:
            raise UserError(_('No water connections selected.'))
        WaterConnection = self.env['wua.waterconnection']
        waterconnections = WaterConnection.browse(active_ids)
        report_name = (
            'base_wua_infrastructure'
            '.wua_waterconnection_technical_sheet_report_document'
        )
        sent_pairs = set()
        for wc in waterconnections:
            # Compute recipients for THIS waterconnection
            partners = self._get_payer_partners(wc)
            if not partners:
                _logger.warning(
                    'Technical sheet wizard: no recipient found for wc %s',
                    wc.name)
                continue
            # Generate PDF
            try:
                pdf_content = self.env['report'].get_pdf([wc.id], report_name)
            except Exception as e:
                _logger.error(
                    'Technical sheet wizard: could not render PDF for wc'
                    ' %s: %s', wc.id, str(e))
                raise UserError(
                    _('Could not generate the technical sheet PDF for %s: %s')
                    % (wc.name, str(e)))
            filename = 'technical_sheet_%s.pdf' % (
                (wc.name or str(wc.id)).replace('/', '_'))
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'datas_fname': filename,
                'res_model': 'wua.waterconnection',
                'res_id': wc.id,
                'mimetype': 'application/pdf',
            })
            for partner in partners:
                pair_key = (wc.id, partner.id)
                if pair_key in sent_pairs:
                    continue
                sent_pairs.add(pair_key)
                ctx = {
                    'partner_name': partner.name or '',
                    'partner_email': partner.email or '',
                }
                rendered_subject = template.with_context(ctx).render_template(
                    self.subject, 'wua.waterconnection', [wc.id])
                rendered_body = template.with_context(ctx).render_template(
                    self.body or '', 'wua.waterconnection', [wc.id])
                mail = self.env['mail.mail'].create({
                    'subject': rendered_subject.get(wc.id) or self.subject,
                    'email_to': partner.email or '',
                    'body_html': rendered_body.get(wc.id) or '',
                    'attachment_ids': [(4, attachment.id)],
                    'auto_delete': True,
                })
                mail.send()
                _logger.info(
                    'Technical sheet sent for wc %s to partner %s (%s)',
                    wc.name, partner.name, partner.email)
        return {'type': 'ir.actions.act_window_close'}
