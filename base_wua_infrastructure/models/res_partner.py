# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    waterconnectionlink_ids = fields.One2many(
        string='Waterconnections',
        comodel_name='res.partner.waterconnection',
        inverse_name='partner_id',
    )

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

    def get_res_partner_waterconnections_action(self):
        context = {}
        current_partner_id = self.env.context.get('active_id')
        if (self.env.user.has_group('base_wua.group_wua_user')):
            context = {
                'is_wua_user': True,
            }
        condition = [('partner_id', '=', current_partner_id)]
        # Check if portal user and thenn only show the ones of
        # condition = [()]
        id_tree_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_tree').id
        id_search_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_search').id
        id_kanban_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_kanban').id
        waterconnections = self.sudo().get_value_from_translation(
            'base_wua_infrastructure',
            'Waterconnections')
        if (not waterconnections):
            waterconnections = _("Waterconnections")
        act_window = {
            'type': 'ir.actions.act_window',
            'name': waterconnections,
            'res_model': 'res.partner.waterconnection',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search'),
                      (id_kanban_view, 'kanban')],
            'target': 'current',
            'context': context,
            'domain': condition,
            }
        return act_window


class ResPartnerWaterconnection(models.Model):
    _name = 'res.partner.waterconnection'
    _auto = False
    _order = 'waterconnection_id'

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',)

    waterconnection_id = fields.Many2one(
        string='Waterconnection',
        comodel_name='wua.waterconnection',)

    description = fields.Char(
        string='Description',
        related='waterconnection_id.description')

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='res_partner_waterconnection')
            """)
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(self.env.cr,
                                      'res_partner_waterconnection')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                CREATE OR REPLACE VIEW res_partner_waterconnection AS (
                SELECT row_number() OVER() AS id, a.* FROM (
                    SELECT wpp1.partner_id, wpi1.waterconnection_id, wpi1.active
                    FROM
                    wua_parcel_irrigationpoint wpi1 INNER JOIN
                    wua_waterconnection ww1 ON ww1.id = wpi1.waterconnection_id
                    INNER JOIN wua_parcel_partnerlink wpp1 ON wpp1.parcel_id =
                    wpi1.parcel_id WHERE wpi1.type='WC'
                    GROUP BY  wpp1.partner_id, wpi1.waterconnection_id, wpi1.active
                ) a )
                """)
        except Exception:
            self.env.cr.rollback()

    def action_show_partner_id(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua.view_partner_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Partners'),
            'res_model': 'res.partner',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.partner_id.id
            }
        return act_window

    def action_show_waterconnection_id(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_infrastructure.wua_waterconnection_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterconnection'),
            'res_model': 'wua.waterconnection',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.waterconnection_id.id
            }
        return act_window
