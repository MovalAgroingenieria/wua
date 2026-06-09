# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
import random
from odoo import models, fields, exceptions, _


class NRSTemplate(models.Model):
    _inherit = 'nrs.template'

    type = fields.Selection(
        selection_add=[('quota', 'Quota')])

    def _get_random_quota(self):
        quota = ""
        quota_ids = self.env['wua.quota'].search([], limit=1000).ids
        if len(quota_ids) > 0:
            random_quota_id = random.choice(quota_ids)
            quota = self.env['wua.quota'].browse(random_quota_id)
        else:
            raise exceptions.ValidationError(_("No quota found"))
        return quota

    def _get_template_render_context_quota(self):
        quota = self._get_random_quota()
        partner = quota.partner_id
        render_context = {
            "partner": partner, "quota": quota, "datetime": datetime}
        return render_context
