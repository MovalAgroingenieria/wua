# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    enable_remotecontrol = fields.Boolean(
        string='Enabled',
        help='if it is marked, it is required set the next url ' +
             '(SERVER URL)')

    url_scada_server = fields.Char(
        string='Server URL',
        size=255)

    scada_server_database = fields.Char(
        string='Database',
        size=255,
        help='Database to get data in remote server')

    scada_server_username = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote server')

    scada_server_password = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote server')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'enable_remotecontrol',
                           self.enable_remotecontrol)
        values.set_default('wua.irrigation.configuration',
                           'url_scada_server',
                           self.url_scada_server)
        values.set_default('wua.irrigation.configuration',
                           'scada_server_database',
                           self.scada_server_database)
        values.set_default('wua.irrigation.configuration',
                           'scada_server_username',
                           self.scada_server_username)
        values.set_default('wua.irrigation.configuration',
                           'scada_server_password',
                           self.scada_server_password)

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
