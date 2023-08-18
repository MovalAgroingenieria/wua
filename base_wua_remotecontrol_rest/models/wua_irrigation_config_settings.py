# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    enable_remotecontrol = fields.Boolean(
        string='Enabled',
        help='if it is marked, it is required set the next url ' +
             '(API REST URL)')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'enable_remotecontrol',
                           self.enable_remotecontrol)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationConfiguration, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            irrigation_model_type = int(self.env['ir.values'].get_default(
                'wua.infrastructure.configuration', 'irrigation_model_type'))
            if irrigation_model_type == 1:
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//group[@name='remote_control']"):
                    node.set('modifiers', '{"invisible": true}')
                res['arch'] = etree.tostring(doc)
        return res

    # Function to be inherited and extended by every telecontrol
    # With super
    def can_be_sent_partners_census_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def can_be_sent_parcels_census_any(self):
        return False

    def import_from_waterconnection_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_from_irrigationshed_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_from_pressuresensor_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_from_hydraulicsector_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_irrigation_event_from_wc_any(self):
        return False

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_irrigation_schedule_from_wc_any(self):
        return False
