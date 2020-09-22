# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    flowmeter_salz_id = fields.Integer(
        string='Salz ID',
        size=3,
        help='The id that identifies the remote Salz flowmeter')

    flowmeter_salz_gid = fields.Integer(
        string='Salz GID',
        size=3,
        help='The group id that identifies the remote Salz flowmeter')

    _sql_constraints = [
        ('negative_flowmeter_id',
         'CHECK (flowmeter_salz_id >= 0)',
         'Flow meter ID can not be negative.'),
        ('negative_flowmeter_gid',
         'CHECK (flowmeter_salz_gid >= 0)',
         'Flow meter GID can not be negative.'),
        ]

    @api.model
    def run_remoteflowmeter_application_url(self):
        enable_remote_flowmeter = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remote_flowmeter')
        if not enable_remote_flowmeter:
            raise exceptions.UserError(
                _('The remote flowmeter is not enabled.'))
        url_remote_flowmeter_app = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remote_flowmeter_app')
        if not url_remote_flowmeter_app:
            raise exceptions.UserError(
                _('There is not a URL for the remote flowmeter application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remote_flowmeter_app,
            'target': 'new', }

    @api.model
    def create(self, vals):
        if 'flowmeter_salz_id' in vals and 'flowmeter_salz_gid' in vals:
            current_flowmeters = self.env['wua.flowmeter'].search([])
            for flowmeter in current_flowmeters:
                if flowmeter.flowmeter_salz_id == vals['flowmeter_salz_id'] \
                    and flowmeter.flowmeter_salz_gid == \
                        vals['flowmeter_salz_gid']:
                    raise exceptions.ValidationError(
                        _('A flowmeter already exists with the same ID / GID '
                          'combination.'))
            new_flowmeter = super(WuaFlowmeter, self).create(vals)
        return new_flowmeter

    @api.multi
    def write(self, vals):
        if 'flowmeter_salz_id' in vals and 'flowmeter_salz_gid' in vals:
            current_flowmeters = self.env['wua.flowmeter'].search([])
            for flowmeter in current_flowmeters:
                if flowmeter.flowmeter_salz_id == vals['flowmeter_salz_id'] \
                    and flowmeter.flowmeter_salz_gid == \
                        vals['flowmeter_salz_gid']:
                    raise exceptions.ValidationError(
                        _('A flowmeter already exists with the same ID / GID '
                          'combination.'))
        return super(WuaFlowmeter, self).write(vals)
