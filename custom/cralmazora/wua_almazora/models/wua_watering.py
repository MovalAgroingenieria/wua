# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaWatering(models.Model):
    _inherit = 'wua.watering'
    _description = 'Waterings'

    def join_gravconsumptions_to_watering_by_distribution(self):
        resp = 0
        subparcels_to_exclude = []
        gravconsumptions_to_exclude = self.env['wua.gravconsumption'].search(
            [('irrigationditch_id', '=', self.irrigationditch_id.id),
             ('wateringperiod_id', '=', self.wateringperiod_id.id)])
        if gravconsumptions_to_exclude:
            for gravconsumption in gravconsumptions_to_exclude:
                subparcel_id = gravconsumption.subparcel_id.id
                if subparcel_id not in subparcels_to_exclude:
                    subparcels_to_exclude.append(subparcel_id)
        condition = [('irrigationditch_id', '=', self.irrigationditch_id.id),
                     ('irrigationgate_id', '!=', False),
                     ('parcel_id.gravityfed_irrigation_right', '=', True),
                     ('parcel_id.with_watering_shift', '=', True)]
        if self.only_cultivable_subparcel:
            condition.append(('is_cultivable', '=', True))
        subparcels = self.env['wua.parcel.subparcel'].search(condition)
        if subparcels:
            for subparcel in subparcels:
                subparcel_id = subparcel.id
                if subparcel_id not in subparcels_to_exclude:
                    gravconsumption_vals = {
                        'subparcel_id': subparcel_id,
                        'wateringperiod_id': self.wateringperiod_id.id,
                        'watering_id': self.id,
                        'state': 'proposed',
                        'gravconsumption_type': 'distribution',
                        'selected': False,
                        }
                    self.env['wua.gravconsumption'].create(
                        gravconsumption_vals)
                    resp = resp + 1
        return resp
