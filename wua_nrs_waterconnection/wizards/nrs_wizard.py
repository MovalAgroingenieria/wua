# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from datetime import datetime
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
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        context = self._context
        if context.get('mode') == 'partner':
            context_filter = "[('type', '=', 'partner')]"
        elif context.get('mode') == 'invoice':
            context_filter = "[('type', '=', 'invoice')]"
        elif context.get('mode') == 'parcel':
            context_filter = "[('type', '=', 'parcel')]"
        elif context.get('mode') == 'waterconnection':
            context_filter = "[('type', '=', 'waterconnection')]"
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
