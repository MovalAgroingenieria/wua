# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
import datetime


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_initial_time_from_reference(self, reference_date):
        parsed_reference = None
        if isinstance(reference_date, datetime.datetime):
            parsed_reference = reference_date
        elif isinstance(reference_date, datetime.date):
            parsed_reference = datetime.datetime.combine(
                reference_date,
                datetime.time.min,
            )
        else:
            reference_text = str(reference_date)
            for date_format in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    parsed_reference = datetime.datetime.strptime(
                        reference_text,
                        date_format,
                    )
                    break
                except ValueError:
                    continue
        if parsed_reference:
            parsed_reference += datetime.timedelta(seconds=1)
        return parsed_reference

    def recalculate_extra_hydric_movements(self):
        active_irrigationpoints = self.env['wua.parcel.irrigationpoint'].search([
            ('active', '=', True),
            ('waterconnection_id.active', '=', True),
            ('partner_id', '!=', False),
        ])
        active_partner_ids = active_irrigationpoints.mapped('partner_id').ids

        if self:
            partners = self.filtered(lambda partner: partner.id in active_partner_ids)
        else:
            partners = self.env['res.partner'].search([
                ('id', 'in', active_partner_ids),
                ('quota_ids', '!=', False),
                ('quota_ids.of_active_agriculturalseason', '=', True),
                ('quota_ids.quotaperiod_id.is_closed', '=', False),
            ])

        active_wc_by_partner = {}
        for irrigation_point in active_irrigationpoints:
            if not irrigation_point.partner_id:
                continue
            active_wc_by_partner.setdefault(
                irrigation_point.partner_id.id,
                set(),
            ).add(irrigation_point.waterconnection_id.id)

        _logger.info(
            "Starting recalculate_extra_hydric_movements for %s partner(s) "
            "with active irrigation points and open quotas",
            len(partners),
        )
        processed_partners = 0
        recalculated_readings = 0
        _logger.info(
            "recalculate_extra_hydric_movements: total candidates=%s",
            len(partners),
        )
        for partner in partners:
            wc_ids = list(active_wc_by_partner.get(partner.id, set()))
            if not wc_ids:
                _logger.debug(
                    "Skipping partner %s: no active irrigation point with "
                    "active water connection",
                    partner.id,
                )
                continue
            quotas = partner.quota_ids.filtered(
                lambda x: x.of_active_agriculturalseason and
                not x.quotaperiod_id.is_closed
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
            initial_time = self._get_initial_time_from_reference(reference_date)
            if not initial_time:
                _logger.warning(
                    "Skipping partner %s: invalid reference date %s",
                    partner.id,
                    reference_date,
                )
                continue
            readings = self.env['wua.controlreading'].search([
                ('waterconnection_id', 'in', wc_ids),
                ('reading_time', '>=', initial_time.strftime('%Y-%m-%d %H:%M:%S'))
            ])
            processed_partners += 1
            recalculated_readings += len(readings)
            _logger.info(
                "recalculate_extra_hydric_movements: partner=%s, "
                "readings_recalculated=%s, total_processed=%s",
                partner.id,
                len(readings),
                processed_partners,
            )
            for reading in readings:
                reading.cancel_controlreading()
                reading.validate_controlreading()
        _logger.info(
            "Finished recalculate_extra_hydric_movements: processed partners=%s, readings=%s",
            processed_partners,
            recalculated_readings,
        )
