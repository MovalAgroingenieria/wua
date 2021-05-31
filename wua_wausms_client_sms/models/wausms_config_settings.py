# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WauSMSConfiguration(models.TransientModel):
    _inherit = 'wausms.configuration'

    default_parcel_template_id = fields.Many2one(
        comodel_name='wausms.template',
        string='Parcel',
        ondelete="set null")

    @api.multi
    def set_default_values(self):
        super(WauSMSConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wausms.configuration',
                           'default_parcel_template_id',
                           self.default_parcel_template_id.id)
