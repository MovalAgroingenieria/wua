# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from jinja2 import Template, TemplateError
from datetime import datetime
import random
from odoo import models, fields, api, exceptions, _


class WauSMSTemplate(models.Model):
    _inherit = 'wausms.template'

    type = fields.Selection(
        selection_add=[('waterconnection', 'Waterconnection')])

    def _get_random_waterconnection(self):
        waterconnection = ""
        waterconnection_ids = \
            self.env['wua.waterconnection'].search([], limit=1000).ids
        if len(waterconnection_ids) > 0:
            random_waterconnection_id = random.choice(waterconnection_ids)
            waterconnection = self.env['wua.waterconnection'].browse(
                random_waterconnection_id)
        else:
            raise exceptions.ValidationError(_("No waterconnection found"))
        return waterconnection

    @api.multi
    def action_resolve_template(self):
        if self.type != 'waterconnection':
            return super(WauSMSTemplate, self).action_resolve_template()
        self.ensure_one()
        template = partner = waterconnection = raw_message = message = ""
        if self.template:
            template = Template(self.template)
        if template and self.type == 'waterconnection':
            waterconnection = self._get_random_waterconnection()
            if waterconnection.irrigationpoint_ids:
                partner = self.env['res.partner'].browse(
                    waterconnection.irrigationpoint_ids[0].partner_id.id)
            else:
                partner = self._get_random_partner()
            try:
                raw_message = template.render(
                    partner=partner, waterconnection=waterconnection,
                    datetime=datetime)
            except TemplateError as err:
                raise exceptions.ValidationError(
                    _("Error resolving template: {}".format(err.message)))
        if raw_message:
            message = self._escape_json_special_chars(raw_message)
        if len(message) > 160:
            raise exceptions.ValidationError(
                _('The size of the SMS after solving the variables exceeds '
                  '160 characters. Try setting a fixed length for variables '
                  '{{ object.attribute[:10] }}'))
        if message:
            self.template_resolved = message
