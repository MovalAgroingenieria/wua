# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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

    nominal_flow_granted = fields.Float(
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
            max_nominal_flow = partner_area * preswatering.proration
            total_nominal_flow_ls = sum(
                c.nominal_flow_ls for c in consumptions)
            # Proration
            if total_nominal_flow_ls > max_nominal_flow:
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
