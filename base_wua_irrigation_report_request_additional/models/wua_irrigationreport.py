# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    source_reportrequest_id = fields.Many2one(
        string='Source Report Request',
        comodel_name='wua.reportrequest',
        index=True,
        store=True,
        ondelete="restrict")

    mapped_to_source_reportrequest_id = fields.Boolean(
        string='Mapped to a source report request',
        store=True,
        compute='_compute_mapped_to_source_reportrequest_id')

    @api.depends('source_reportrequest_id')
    def _compute_mapped_to_source_reportrequest_id(self):
        for record in self:
            mapped_to_source_reportrequest_id = False
            if record.source_reportrequest_id:
                mapped_to_source_reportrequest_id = True
            record.mapped_to_source_reportrequest_id = \
                mapped_to_source_reportrequest_id
