# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import UserError
import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def recalculate_extra_hydric_movements(self):
        for partner in self:
            quotas = partner.quota_ids.filtered(
                lambda x: x.of_active_agriculturalseason and not x.quotaperiod_id.is_closed
            )
            if not quotas:
                continue

            last_move = self.env['wua.hydricmovement'].search([
                ('quota_id', 'in', quotas.ids),
                ('type', '=', 'pres_consumption')
            ], order='event_time desc', limit=1)

            if not last_move:
                continue

            try:
                initial_time = datetime.datetime.strptime(
                    last_move.event_time, '%Y-%m-%d %H:%M:%S'
                ) + datetime.timedelta(seconds=1)
            except Exception:
                continue

            wc_ids = self.env['wua.waterconnection'].search([
                ('irrigationpoint_ids.partner_id', '=', partner.id)
            ])
            for wc in wc_ids:
                partners = wc.irrigationpoint_ids.mapped('partner_id')
                if len(partners) > 1:
                    raise UserError_(
                        "The waterconnection has multiple partners and cannot be recalculated automatically."
                    )

            readings = self.env['wua.controlreading'].search([
                ('waterconnection_id', 'in', wc_ids.ids),
                ('reading_time', '>=', initial_time.strftime('%Y-%m-%d %H:%M:%S'))
            ])
            for reading in readings:
                reading.cancel_controlreading()
                reading.validate_controlreading()
