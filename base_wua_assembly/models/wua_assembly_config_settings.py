# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAssemblyindexConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.assembly.configuration'
    _description = 'Configuration of base_wua_assembly module'

    assembly_street = fields.Char(
        string='Street',)

    assembly_zip = fields.Char(
        string='Zip Code',)

    assembly_city = fields.Char(
        string='City',)

    assembly_state_id = fields.Many2one(
        string='Province',
        comodel_name='res.country.state',
        ondelete='restrict',)

    assembly_country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        ondelete='restrict',)

    assembly_president_id = fields.Many2one(
        string='President',
        comodel_name='res.users',
        domain=[('is_wua_user', '=', True)],
        required=True,)

    assembly_secretary_id = fields.Many2one(
        string='Secretary',
        comodel_name='res.users',
        domain=[('is_wua_user', '=', True)],
        required=True,)

    vat_required = fields.Boolean(
        string='TIN required',
        default=False,
        required=True,)

    allow_notes_in_signature = fields.Boolean(
        string='Allow notes with the partner signature',
        default=True,
        required=True,)
    
    add_qr_code_in_attendance = fields.Boolean(
        string='Add qr code in attendance',
        default=True,)

    @api.onchange('assembly_state_id')
    def _onchange_assembly_state_id(self):
        if not self.assembly_country_id:
            self.assembly_country_id = self.assembly_state_id.country_id

    @api.onchange('assembly_country_id')
    def _onchange_assembly_country_id(self):
        if self.assembly_country_id:
            return {'domain': {'assembly_state_id':
                               [('country_id', '=',
                                 self.assembly_country_id.id)]}}
        else:
            return {'domain': {'assembly_state_id': []}}

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.assembly.configuration',
                           'assembly_street', self.assembly_street)
        values.set_default('wua.assembly.configuration',
                           'assembly_zip', self.assembly_zip)
        values.set_default('wua.assembly.configuration',
                           'assembly_city', self.assembly_city)
        values.set_default('wua.assembly.configuration',
                           'assembly_state_id', self.assembly_state_id.id)
        values.set_default('wua.assembly.configuration',
                           'assembly_country_id', self.assembly_country_id.id)
        values.set_default('wua.assembly.configuration',
                           'assembly_president_id',
                           self.assembly_president_id.id)
        values.set_default('wua.assembly.configuration',
                           'assembly_secretary_id',
                           self.assembly_secretary_id.id)
        values.set_default('wua.assembly.configuration',
                           'vat_required', self.vat_required)
        values.set_default('wua.assembly.configuration',
                           'allow_notes_in_signature',
                           self.allow_notes_in_signature)
        values.set_default('wua.assembly.configuration',
                           'add_qr_code_in_attendance',
                           self.add_qr_code_in_attendance)
