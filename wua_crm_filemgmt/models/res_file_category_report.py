# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ResFileCategoryReport(models.Model):
    _name = 'res.file.category.report'
    _description = "Report of Categories of Files"

    name = fields.Char(
        string='Category Report Name',
        size=50,
        required=True,
        translate=True,
        index=True)

    category_id = fields.Many2one(
        string='Category',
        comodel_name='res.file.category',
        required=True)

    iractreportxml_id = fields.Many2one(
        string='Template base',
        comodel_name='ir.actions.report.xml',
        domain=[('model', '=', 'res.file'),
                ('report_type', '=', 'qweb-pdf')])

    report_template_start = fields.Html(
        string='Template start',
        translate=True)

    report_template_end = fields.Html(
        string='Template end',
        translate=True)

    file_ids = fields.One2many(
        string='Files',
        comodel_name='res.file',
        inverse_name='category_report_id')

    notes = fields.Html(
        string='Notes')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing category report name.'),
        ]
