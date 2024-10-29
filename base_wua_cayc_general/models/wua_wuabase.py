# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWuabase(models.Model):
    _inherit = ['wua.mastertable', 'mail.thread']
    _name = 'wua.wuabase'
    _description = 'Entity (Primary Entity)'
    _order = 'name'

    _size_name = 3
    _size_description = 255
    _numeric_name = True

    name = fields.Char(
        string='Primary Entity',
    )

    partner_ids = fields.One2many(
        string='WUA Partners',
        comodel_name='res.partner',
        inverse_name='wuabase_id',
    )

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='wuabase_id',
    )

    parcel_mapped_ids = fields.One2many(
        string='Parcels Mapped',
        comodel_name='wua.parcel',
        inverse_name='wuabase_id',
        domain=[('mapped_parcel', '=', True)],
    )

    parcel_class_ids = fields.One2many(
        string='Parcel Classes',
        comodel_name='wua.parcel.class',
        inverse_name='wuabase_id',
    )

    server_remote_ip = fields.Char(
        string='Server Remote IP',
        size=254,
    )

    server_remote_port = fields.Char(
        string='Server Remote Port',
        size=254,
    )

    server_remote_database = fields.Char(
        string='Server Remote Database',
        size=254,
    )

    server_remote_database_user = fields.Char(
        string='Server Remote Database User',
        size=254,
    )

    server_remote_database_password = fields.Char(
        string='Server Remote Database Password',
        size=254,
    )

    server_connected = fields.Boolean(
        string='Connected',
        compute='_compute_server_connected',
        store=True,
    )

    last_syncrhonization_date = fields.Datetime(
        string='Last Syncrhonization Date',
    )

    @api.depends(
        'server_remote_ip', 'server_remote_port', 'server_remote_database',
        'server_remote_database_user', 'server_remote_database_password')
    def _compute_server_connected(self):
        for record in self:
            server_connected = False
            if (record.server_remote_ip and record.server_remote_port and
                record.server_remote_database and
                record.server_remote_database_user and
                    record.server_remote_database_password):
                server_connected = True
            record.server_connected = server_connected

    @api.multi
    def do_synchronization_from_wuabase(self):
        model_partner = self.env['res.partner']
        for record in self:
            if record.server_connected:
                model_partner.refresh_partners_of_wuabase(record)

    def name_get(self):
        result = []
        for record in self:
            description = u''
            if (record.description):
                description = record.description
            display_name = u'[' + record.name + u'] ' + description
            result.append((record.id, display_name))
        return result
