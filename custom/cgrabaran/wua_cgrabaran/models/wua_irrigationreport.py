# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from bs4 import BeautifulSoup
from odoo import models, fields, api, _


class WuaIrrigationreport(models.Model):
    _inherit = 'wua.irrigationreport'

    area_total_company_g = fields.Float(
        string='Area of Grupo (ha)',
        related='partner_id.area_total_company_g')

    area_total_company_r = fields.Float(
        string='Area of Resurrección (ha)',
        related='partner_id.area_total_company_r')

    area_total_company_t = fields.Float(
        string='Area of Trasvase (ha)',
        related='partner_id.area_total_company_t')

    @api.onchange('partner_id')
    def _onchange_intake_id(self):
        for record in self:
            intakes = []
            if record.area_total_company_g != 0.0:
                company_01_id = self.env['ir.values'].get_default(
                    'wua.configuration', 'company_01')
                intake_g = self.env['wua.intake'].search([
                    ('company_id', '=', company_01_id)])
                intakes += intake_g
            if record.area_total_company_r != 0.0:
                company_02_id = self.env['ir.values'].get_default(
                    'wua.configuration', 'company_02')
                intake_r = self.env['wua.intake'].search([
                    ('company_id', '=', company_02_id)])
                intakes += intake_r
            if record.area_total_company_t != 0.0:
                company_03_id = self.env['ir.values'].get_default(
                    'wua.configuration', 'company_03')
                intake_t = self.env['wua.intake'].search([
                    ('company_id', '=', company_03_id)])
                intakes += intake_t
            if len(intakes) == 1:
                record.intake_id = intakes[0].id
            else:
                record.intake_id = False


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # Extend original method
    def get_description(self, irrigationreport):
        description = \
            super(WuaInvoiceset, self).get_description(irrigationreport)
        notes = irrigationreport.notes
        if notes:
            notes_raw = BeautifulSoup(notes, features="html.parser")
            notes = notes_raw.get_text()
            description += '. ' + _('NOTE: ') + notes
        return description
