# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pytz
import logging
from datetime import timedelta
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class WuaPresreswatering(models.Model):
    _inherit = 'wua.preswatering'

    proration = fields.Float(
        string="Proration",
        required=True,
        digits=(32, 2),
    )

    zones_united = fields.Boolean(
        string="Zones United",
        default=False,
    )

    rebombed_flow_ls = fields.Float(
        string="Rebombed Flow (l/s)",
        digits=(32, 0),
        default=0.0,
    )

    by_gravity_outlet = fields.Boolean(
        string="By Gravity Outlet",
        default=False,
    )

    by_pumping = fields.Boolean(
        string="By Pumping",
        default=False,
    )

    by_surplus = fields.Boolean(
        string="By Surplus",
        default=False,
    )

    nominal_flow_requested = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_requested = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_granted = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_issued = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_issued = fields.Float(
        digits=(32, 0),
    )

    _sql_constraints = [
        ('check_proration_positive',
         'CHECK(proration > 0)',
         'The value of \'Proration\' must be greater than 0.'),
    ]

    @api.onchange('preswateringperiod_id')
    def _onchange_preswateringperiod_id(self):
        if self.preswateringperiod_id:
            self.proration = self.preswateringperiod_id.proration

    def _process_granted_nominal_flows(
            self, presresconsumptions, preswatering):
        presres_grouped = {}
        # Group by wateringrequest
        for presresconsumption in presresconsumptions:
            key = presresconsumption.preswateringrequest_id
            if key not in presres_grouped:
                presres_grouped[key] = []
            presres_grouped[key].append(presresconsumption)
        # Calculation
        for preswateringrequest_id, consumptions in presres_grouped.items():
            partner_area = preswateringrequest_id.partner_parcel_owner_area
            is_wua_type = preswateringrequest_id.partner_id.partner_type == \
                '01_WUA'
            max_nominal_flow = partner_area * preswatering.proration
            total_nominal_flow_ls = sum(
                c.nominal_flow_ls for c in consumptions)
            # Proration
            if total_nominal_flow_ls > max_nominal_flow and is_wua_type:
                for consumption in consumptions:
                    requested_flow = consumption.nominal_flow_ls
                    prorated_flow = (requested_flow * max_nominal_flow) / \
                        total_nominal_flow_ls
                    # Floor to the nearest 5
                    prorated_flow_rounded = 5 * (
                        (prorated_flow + 2.5) // 5)
                    consumption.write({
                        'nominal_flow_granted': prorated_flow_rounded * 3.6,
                        'nominal_flow_ls_granted': prorated_flow_rounded,
                    })
            else:
                for consumption in consumptions:
                    consumption.write({
                        'nominal_flow_granted': consumption.nominal_flow,
                        'nominal_flow_ls_granted': consumption.nominal_flow_ls,
                    })

    @api.multi
    def validate_presresconsumptions(self):
        self.ensure_one()
        # Check if hours are correct to send data
        initial_time_utc = fields.Datetime.from_string(self.initial_time)
        spain_tz = pytz.timezone('Europe/Madrid')
        initial_time_sp = pytz.utc.localize(
            initial_time_utc).astimezone(spain_tz)
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        current_time_sp = pytz.utc.localize(current_time_utc_dt).astimezone(
            spain_tz)
        if (
            initial_time_sp.date() == current_time_sp.date() and
            current_time_sp.hour >= 8
        ):
            return super(WuaPresreswatering, self).\
                validate_presresconsumptions()
        else:
            raise exceptions.UserError(_(
                'You can only validate the consumptions on request day '
                'starting at 08:00'))

    @api.multi
    def issue_presresconsumptions(self):
        self.ensure_one()
        initial_time_utc = fields.Datetime.from_string(self.initial_time)
        spain_tz = pytz.timezone('Europe/Madrid')
        initial_time_sp = pytz.utc.localize(initial_time_utc).astimezone(
            spain_tz)
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        current_time_sp = pytz.utc.localize(current_time_utc_dt).astimezone(
            spain_tz)
        today_0800_sp = current_time_sp.replace(
            hour=8, minute=0, second=0, microsecond=0)
        valid_start = (today_0800_sp - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        valid_end = today_0800_sp
        if valid_start <= initial_time_sp < valid_end:
            return super(WuaPresreswatering, self).issue_presresconsumptions()
        else:
            raise exceptions.UserError(_(
                'You can only issue the consumptions from the previous day '
                'until 08:00 of the current day'))

    @api.model
    def get_sinema_issued_consumptions(self):
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        spain_tz = pytz.timezone('Europe/Madrid')
        current_time_sp = pytz.utc.localize(current_time_utc_dt).astimezone(
            spain_tz)
        today_0800_sp = current_time_sp.replace(
            hour=8, minute=0, second=0, microsecond=0)
        valid_start = (today_0800_sp - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        valid_end = today_0800_sp
        valid_start_utc = valid_start.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        valid_end_utc = valid_end.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        preswaterings = self.search([
            ('initial_time', '>=', valid_start_utc),
            ('initial_time', '<', valid_end_utc),
            ('state', '=', '02_validated'),
        ])
        for preswatering in preswaterings:
            try:
                preswatering.issue_presresconsumptions()
            except Exception as e:
                _logger.error(
                    'Error issuing preswatering %s: %s', preswatering, e)
