# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    # Hook ("False" when the consumption is not validated)
    def is_valid_presconsumption(self, updated_presconsumption):
        resp = updated_presconsumption.validated
        return resp
