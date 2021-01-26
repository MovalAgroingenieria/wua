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

    @api.multi
    def validate_irrigationreport(self):
        super(WuaIrrigationReport, self).validate_irrigationreport()
        self.ensure_one()
        report = self
        if not report.source_reportrequest_id:
            report.source_reportrequest_id = report.reportrequest_id
