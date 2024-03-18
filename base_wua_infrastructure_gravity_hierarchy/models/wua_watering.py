# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaWatering(models.Model):
    _inherit = 'wua.watering'

    # Hook: This method is called from descendant classes to refine
    # the condition to find gravity-consumptions in the
    # "join_gravconsumptions_to_watering_by_request" method, find subparcels
    # in the "join_gravconsumptions_to_watering_by_distribution" method,
    # and find irrigation-gates in the "calculate_durations" method.
    # Here you need to change the "irrigationditch_id" field to the
    # "main_irrigationditch_id" field.
    def _update_condition(self, condition):
        resp = [('id', '=', False)]
        if condition:
            resp = []
            for condition_item in (condition or []):
                if len(condition_item) == 3:
                    item_01 = condition_item[0]
                    item_02 = condition_item[1]
                    item_03 = condition_item[2]
                    # Modified EIS (2024-03-18)
                    # This is not necessary! (remove method?)
                    # if item_01 == 'irrigationditch_id':
                    #     item_01 = 'main_irrigationditch_id'
                    resp_item = (item_01, item_02, item_03)
                    resp.append(resp_item)
        return resp
