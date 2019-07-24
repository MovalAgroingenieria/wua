# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    enable_remotecontrol = fields.Boolean(
        string='Remote Control enabled',
        help='if it is marked, it is required set the next url ' +
             '(API REST URL)')

    url_remotecontrol_rest = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_application = fields.Char(
        string='Native Application URL',
        size=255)

    can_be_sent_partners_census = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection = fields.Boolean(
        string='Import from water connection')

    import_from_irrigationshed = fields.Boolean(
        string='Import from irrigation shed')

    import_from_hydraulicsector = fields.Boolean(
        string='Import from hydraulic sector')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'enable_remotecontrol',
                           self.enable_remotecontrol)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest',
                           self.url_remotecontrol_rest)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application',
                           self.url_remotecontrol_application)

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
