# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
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
        if context.get("mode") == 'waterconnection':
            default_template_id = self.env['ir.values'].get_default(
                'nrs.configuration', 'default_waterconnection_template_id')
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
        if self._context.get('mode') == 'waterconnection':
            domain = "[('type', '=', 'waterconnection')]"
        return domain

    def _get_targets_waterconnection(self, context):
        targets = []
        seen = []
        waterconnections = self.env['wua.waterconnection'].browse(
            context.get('active_ids'))
        for waterconnection in waterconnections:
            for irrigationpoint in waterconnection.irrigationpoint_ids:
                partner = irrigationpoint.partner_id
                if not partner:
                    continue
                key = (partner.id, waterconnection.id)
                if key in seen:
                    continue
                seen.append(key)
                target = {
                    "partner": partner,
                    "render_context": {
                        "partner": partner, "invoice": "", "parcel": "",
                        "waterconnection": waterconnection,
                        "datetime": datetime},
                    "ref": waterconnection.name or "",
                    "append_text": "",
                    "tracking": {
                        "partner_id": partner.id, "invoice_id": "",
                        "waterconnection_id": waterconnection.id},
                }
                targets.append(target)
        return targets
