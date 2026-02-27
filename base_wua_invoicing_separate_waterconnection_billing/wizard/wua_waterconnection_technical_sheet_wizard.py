# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class WuaWaterconnectionTechnicalSheetWizard(models.TransientModel):
    _inherit = 'wua.waterconnection.technical.sheet.wizard'

    @api.model
    def _get_payer_partners(self, wc):
        """Use watercosts_partner_id when available.

        If the waterconnection has a specific water-costs partner assigned
        (computed from parcel partnerlinks), use it directly. Otherwise
        fall back to the base logic.
        """
        if wc.watercosts_partner_id:
            return wc.watercosts_partner_id
        return super(WuaWaterconnectionTechnicalSheetWizard,
                     self)._get_payer_partners(wc)
