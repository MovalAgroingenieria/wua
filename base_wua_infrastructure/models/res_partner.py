# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner of a WUA with irrigation infrastructure'

    def get_res_partner_irrigationpoints_action(self):
        current_partner_id = self.env.context.get('active_id')
        parcel_ids = []
        irrigationpoint_ids = []
        parcel_partnerlinks = self.env['wua.parcel.partnerlink']
        parcel_irrigation_points = self.env['wua.parcel.irrigationpoint']
        filtered_parcel_partnerlinks = \
            parcel_partnerlinks.search(
                [('partner_id', '=', current_partner_id)])
        for partnerlink in filtered_parcel_partnerlinks:
            parcel_ids.append(partnerlink.parcel_id.id)
        if len(parcel_ids) > 0:
            filtered_parcel_irrigation_points = \
                parcel_irrigation_points.search(
                    [('parcel_id', 'in', parcel_ids)])
            for irrigationpoint in filtered_parcel_irrigation_points:
                irrigationpoint_ids.append(irrigationpoint.id)
        condition = [('id', 'in', irrigationpoint_ids)]
        id_tree_view = \
            self.env.ref('base_wua_infrastructure.'
                         'wua_parcel_irrigationpoint_view_tree').id
        id_search_view = \
            self.env.ref('base_wua_infrastructure.'
                         'wua_parcel_irrigationpoint_view_search').id
        irrigation_points_name = self.sudo().get_value_from_translation(
            'base_wua_infrastructure',
            self.env['wua.parcel'].__class__.irrigationpoint_ids.string)
        act_window = {
            'type': 'ir.actions.act_window',
            'name': irrigation_points_name,
            'res_model': 'wua.parcel.irrigationpoint',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': self.env.context,
            }
        return act_window
