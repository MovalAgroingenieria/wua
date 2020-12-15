# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.infrastructure.configuration'
    _description = 'Configuration of base_wua_infrastructure module'

    irrigation_model_type = fields.Selection([
        (0, 'Pressurized Irrigation'),
        (1, 'Gravity Irrigation'),
        (2, 'Both types')],
        'Irrigation Model Type',
        help='Irrigation types used in this water user association')

    url_gis_googlemaps = fields.Char(
        string='Google Maps URL',
        size=255,
        help='Note: ycval and xcval are parameters')

    url_gis_viewer_irrigationshed_param = fields.Char(
        string='Param for irr. shed',
        size=20,
        help='Name of irrigation-shed param in the GIS viewer url')

    url_gis_viewer_waterconnection_param = fields.Char(
        string='Param for waterconnection',
        size=20,
        help='Name of irrigation-shed param in the GIS viewer url')

    url_gis_viewer_irrigationditch_param = fields.Char(
        string='Param for irr. ditch',
        size=20,
        help='Name of irrigation-ditch param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'irrigation_model_type',
                           self.irrigation_model_type)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_googlemaps',
                           self.url_gis_googlemaps)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_irrigationshed_param',
                           self.url_gis_viewer_irrigationshed_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_irrigationditch_param',
                           self.url_gis_viewer_irrigationditch_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_waterconnection_param',
                           self.url_gis_viewer_waterconnection_param)
        self.assign_groups_id_to_menus()

    def assign_groups_id_to_menus(self):
        id_group_no_pressurized_irrigation = 0
        id_group_no_gravityfed_irrigation = 0
        id_base_wua_inf_pressurized_irrig_menu = 0
        id_base_wua_inf_gravityfed_irrig_menu = 0
        try:
            id_group_no_pressurized_irrigation = \
                self.env.ref('base_wua_infrastructure.'
                             'group_no_pressurized_irrigation').id
            id_group_no_gravityfed_irrigation = \
                self.env.ref('base_wua_infrastructure.'
                             'group_no_gravityfed_irrigation').id
            id_base_wua_inf_pressurized_irrig_menu = \
                self.env.ref('base_wua_infrastructure.'
                             'base_wua_infrastructure_'
                             'pressurized_irrigation_menu').id
            id_base_wua_inf_gravityfed_irrig_menu = \
                self.env.ref('base_wua_infrastructure.'
                             'base_wua_infrastructure_'
                             'gravityfed_irrigation_menu').id
        except Exception:
            id_group_no_pressurized_irrigation = 0
            id_group_no_gravityfed_irrigation = 0
            id_base_wua_inf_pressurized_irrig_menu = 0
            id_base_wua_inf_gravityfed_irrig_menu = 0
        if id_group_no_pressurized_irrigation > 0 and \
           id_group_no_gravityfed_irrigation > 0 and \
           id_base_wua_inf_pressurized_irrig_menu > 0 and \
           id_base_wua_inf_gravityfed_irrig_menu > 0:
            irrigation_model_type = int(self.irrigation_model_type)
            if irrigation_model_type == 0:
                strsql = 'DELETE FROM ir_ui_menu_group_rel WHERE menu_id=' + \
                         str(id_base_wua_inf_pressurized_irrig_menu) + \
                         ' and gid=' + \
                         str(id_group_no_pressurized_irrigation)
                self.env.cr.execute(strsql)
                strsql = 'SELECT menu_id, gid FROM ir_ui_menu_group_rel' + \
                    ' WHERE menu_id = ' + \
                    str(id_base_wua_inf_gravityfed_irrig_menu) + \
                    ' AND gid = ' + \
                    str(id_group_no_gravityfed_irrigation)
                self.env.cr.execute(strsql)
                if len(self.env.cr.fetchall()) == 0:
                    strsql = 'INSERT INTO ir_ui_menu_group_rel' + \
                        '(menu_id, gid) VALUES (' + \
                        str(id_base_wua_inf_gravityfed_irrig_menu) + \
                        ', ' + \
                        str(id_group_no_gravityfed_irrigation) + ')'
                    self.env.cr.execute(strsql)
            if irrigation_model_type == 1:
                strsql = 'DELETE FROM ir_ui_menu_group_rel WHERE menu_id=' + \
                         str(id_base_wua_inf_gravityfed_irrig_menu) + \
                         ' and gid=' + \
                         str(id_group_no_gravityfed_irrigation)
                self.env.cr.execute(strsql)
                strsql = 'SELECT menu_id, gid FROM ir_ui_menu_group_rel' + \
                    ' WHERE menu_id = ' + \
                    str(id_base_wua_inf_pressurized_irrig_menu) + \
                    ' AND gid = ' + \
                    str(id_group_no_pressurized_irrigation)
                self.env.cr.execute(strsql)
                if len(self.env.cr.fetchall()) == 0:
                    strsql = 'INSERT INTO ir_ui_menu_group_rel' + \
                        '(menu_id, gid) VALUES (' + \
                        str(id_base_wua_inf_pressurized_irrig_menu) + \
                        ', ' + \
                        str(id_group_no_pressurized_irrigation) + ')'
                    self.env.cr.execute(strsql)
            if irrigation_model_type == 2:
                strsql = 'DELETE FROM ir_ui_menu_group_rel WHERE menu_id=' + \
                         str(id_base_wua_inf_pressurized_irrig_menu) + \
                         ' and gid=' + \
                         str(id_group_no_pressurized_irrigation)
                self.env.cr.execute(strsql)
                strsql = 'DELETE FROM ir_ui_menu_group_rel WHERE menu_id=' + \
                         str(id_base_wua_inf_gravityfed_irrig_menu) + \
                         ' and gid=' + \
                         str(id_group_no_gravityfed_irrigation)
                self.env.cr.execute(strsql)
