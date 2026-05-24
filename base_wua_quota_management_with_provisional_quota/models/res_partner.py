# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
from odoo.exceptions import UserError
import datetime


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def recalculate_extra_hydric_movements(self):
        partners = self or self.env['res.partner'].search([])
        _logger.info(
            "Starting recalculate_extra_hydric_movements for %s partner(s)",
            len(partners),
        )
        processed_partners = 0
        recalculated_readings = 0
        for partner in partners:
            quotas = partner.quota_ids.filtered(
                lambda x: x.of_active_agriculturalseason and not x.quotaperiod_id.is_closed
            )
            if not quotas:
                _logger.debug(
                    "Skipping partner %s: no active quotas in open period",
                    partner.id,
                )
                continue
            last_move = self.env['wua.hydricmovement'].search([
                ('quota_id', 'in', quotas.ids),
                ('type', '=', 'pres_consumption')
            ], order='event_time desc', limit=1)
            if not last_move:
                quotaperiod = quotas.mapped('quotaperiod_id')
                if quotaperiod and quotaperiod[0].initial_date:
                    reference_date = quotaperiod[0].initial_date
                else:
                    _logger.warning(
                        "Skipping partner %s: no last movement and no initial date",
                        partner.id,
                    )
                    continue
            else:
                reference_date = last_move.event_time
            try:
                initial_time = datetime.datetime.strptime(
                    str(reference_date), '%Y-%m-%d %H:%M:%S'
                ) + datetime.timedelta(seconds=1)
            except Exception as exc:
                _logger.warning(
                    "Skipping partner %s: invalid reference date %s (%s)",
                    partner.id,
                    reference_date,
                    exc,
                )
                continue
            wc_ids = self.env['wua.waterconnection'].search([
                ('irrigationpoint_ids.partner_id', '=', partner.id)
            ])
            readings = self.env['wua.controlreading'].search([
                ('waterconnection_id', 'in', wc_ids.ids),
                ('reading_time', '>=', initial_time.strftime('%Y-%m-%d %H:%M:%S'))
            ])
            processed_partners += 1
            recalculated_readings += len(readings)
            for reading in readings:
                reading.cancel_controlreading()
                reading.validate_controlreading()
        _logger.info(
            "Finished recalculate_extra_hydric_movements: processed partners=%s, readings=%s",
            processed_partners,
            recalculated_readings,
        )
