# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
import random
from odoo import models, fields, exceptions, _


class NRSTemplate(models.Model):
    _inherit = "nrs.template"

    type = fields.Selection(
        selection_add=[("parcel", "Parcel")])

    def _get_random_parcel(self):
        parcel = ""
        parcel_ids = self.env["wua.parcel"].search([], limit=1000).ids
        if len(parcel_ids) > 0:
            random_parcel_id = random.choice(parcel_ids)
            parcel = self.env["wua.parcel"].browse(random_parcel_id)
        else:
            raise exceptions.ValidationError(_("No parcel found"))
        return parcel

    def _get_template_render_context_parcel(self):
        parcel = self._get_random_parcel()
        partner = parcel.partner_id
        render_context = {
            "partner": partner, "parcel": parcel, "datetime": datetime}
        return render_context
