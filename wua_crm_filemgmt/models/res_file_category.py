# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ResFileCategory(models.Model):
    _inherit = 'res.file.category'

    category_reports_ids = fields.One2many(
        string='Category reports',
        comodel_name='res.file.category.report',
        inverse_name='category_id')
