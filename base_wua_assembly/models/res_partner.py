# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.modules import get_module_resource
from odoo import models, fields, api, exceptions, _, tools


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    assembly_excluded = fields.Boolean(
        string='Assembly Excluded',
        help="If checked, this partner will not be included in the assembly "
             "process.",
        default=False,
    )