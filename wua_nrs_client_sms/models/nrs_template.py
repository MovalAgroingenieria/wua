# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from jinja2 import Template, TemplateError
from datetime import datetime
import random
from odoo import models, fields, api, exceptions, _


class NRSTemplate(models.Model):
    _inherit = 'nrs.template'

    type = fields.Selection(
        selection_add=[('parcel','Parcel')])

    def _get_random_parcel(self):
        parcel = ""
        parcel_ids = self.env['wua.parcel'].search([], limit=1000).ids
        if len(parcel_ids) > 0:
            random_parcel_id = random.choice(parcel_ids)
            parcel = self.env['wua.parcel'].browse(random_parcel_id)
        else:
            raise exceptions.ValidationError(_("No parcel found"))
        return parcel

    @api.multi
    def action_resolve_template(self):
        if self.type != 'parcel':
            return super(NRSTemplate, self).action_resolve_template()
        self.ensure_one()
        template = partner = parcel = raw_message = message = ""
        if self.template:
            template = Template(self.template)
        if template and self.type == 'parcel':
            parcel = self._get_random_parcel()
            partner = self.env['res.partner'].browse(parcel.partner_id.id)
            try:
                raw_message = template.render(
                    partner=partner, parcel=parcel, datetime=datetime)
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
