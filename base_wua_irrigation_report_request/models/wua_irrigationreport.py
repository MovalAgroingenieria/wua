# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    reportrequest_ids = fields.One2many(
        string='Report Requests',
        comodel_name='wua.reportrequest',
        inverse_name='irrigationreport_id')

    reportrequest_id = fields.Many2one(
        string='Report Request',
        comodel_name='wua.reportrequest',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_reportrequest_id')

    mapped_to_reportrequest = fields.Boolean(
      string='Mapped to a report request',
      store=True,
      compute='_compute_mapped_to_reportrequest')

    @api.depends('reportrequest_ids')
    def _compute_reportrequest_id(self):
        for record in self:
            reportrequest_id = None
            if record.reportrequest_ids:
                reportrequest_id = record.reportrequest_ids[0]
            record.reportrequest_id = reportrequest_id

    @api.depends('reportrequest_id')
    def _compute_mapped_to_reportrequest(self):
        for record in self:
            mapped_to_reportrequest = False
            if record.reportrequest_id:
                mapped_to_reportrequest = True
            record.mapped_to_reportrequest = mapped_to_reportrequest
