# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from datetime import datetime


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
        if context.get("mode") == 'quota':
            default_template_id = self.env['ir.values'].get_default(
                'nrs.configuration', 'default_quota_template_id')
        return default_template_id

    # Overwrite parent field
    template_id = fields.Many2one(
        comodel_name='nrs.template',
        string='Template',
        default=_get_default_template_id,
        ondelete="set null")

    @api.model
    def _get_template_type_domain(self):
        domain = super(NRSWizard, self)._get_template_type_domain()
        if self._context.get('mode') == 'quota':
            domain = "[('type', '=', 'quota')]"
        return domain

    def _get_targets_quota(self, context):
        targets = []
        quotas = self.env['wua.quota'].browse(context.get('active_ids'))
        for quota in quotas:
            partner = quota.partner_id
            target = {
                "partner": partner,
                "render_context": {
                    "partner": partner, "invoice": "", "parcel": "",
                    "quota": quota, "datetime": datetime},
                "ref": quota.name or "",
                "append_text": "",
                "tracking": {
                    "partner_id": partner.id, "invoice_id": "",
                    "quota_id": quota.id},
            }
            targets.append(target)
        return targets
