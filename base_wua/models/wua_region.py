# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaRegion(models.Model):
    _name = 'wua.region'
    _description = 'Region'
    _order = 'code'

    name = fields.Char(
        string='Region Name',
        size=50,
        required=True,
        index=True)

    code = fields.Char(
        string='Region Code',
        size=2,
        required=True)

    image = fields.Binary(attachment=True)

    state_ids = fields.One2many(
        string='States',
        comodel_name='wua.region.state',
        inverse_name='region_id')

    number_of_states = fields.Integer(
        string='Number of states',
        compute='_compute_number_of_states')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Region Name.'),
        ('unique_code', 'UNIQUE (code)', 'Existing Region Code.'),
        ]

    @api.multi
    def _compute_number_of_states(self):
        for record in self:
            record.number_of_states = len(record.state_ids)

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Region Name.'))

    @api.constrains('code')
    def _check_code(self):
        code_no_blanks = self.code.strip()
        if code_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Code.'))
        try:
            proposed_code = int(code_no_blanks)
        except:
            proposed_code = 0
        if proposed_code <= 0:
            raise exceptions.ValidationError(_('The code must be a ' +
                                               'positive value.'))

    @api.model
    def create(self, vals):
        name_no_blanks = vals['name'].strip()
        code_no_blanks = vals['code'].strip()
        if len(code_no_blanks) < 2:
            code_no_blanks = '0' + code_no_blanks
        if name_no_blanks != vals['name']:
            vals.update({'name': name_no_blanks})
        if code_no_blanks != vals['code']:
            vals.update({'code': code_no_blanks})
        return super(WuaRegion, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            name_no_blanks = vals['name'].strip()
            if name_no_blanks != vals['name']:
                vals.update({'name': name_no_blanks})
        if 'code' in vals:
            code_no_blanks = vals['code'].strip()
            if len(code_no_blanks) < 2:
                code_no_blanks = '0' + code_no_blanks
            if code_no_blanks != vals['code']:
                vals.update({'code': code_no_blanks})
        return super(WuaRegion, self).write(vals)


class WuaRegionState(models.Model):
    _name = 'wua.region.state'
    _description = 'State'
    _order = 'cadastral_code'

    name = fields.Char(
        string='State Name',
        size=50,
        required=True,
        index=True)

    cadastral_code = fields.Char(
        string='Cadastral Code',
        size=2,
        help='Two digits of the official cadastral code.',
        required=True)

    region_id = fields.Many2one(
        string='Region',
        comodel_name='wua.region',
        required=True,
        ondelete='restrict')

    region_code = fields.Char(
        string='Region Code',
        related='region_id.code')

    county_ids = fields.One2many(
        string='Counties',
        comodel_name='wua.region.state.county',
        inverse_name='state_id')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Region Name.'),
        ('unique_cadastral_code', 'UNIQUE (cadastral_code)',
         'Existing Cadastral Code.'),
        ]

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty State Name.'))

    @api.constrains('cadastral_code')
    def _check_cadastral_code(self):
        cadastral_code_no_blanks = self.cadastral_code.strip()
        if cadastral_code_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Cadastral Code.'))
        try:
            proposed_cadastral_code = int(cadastral_code_no_blanks)
        except:
            proposed_cadastral_code = 0
        if proposed_cadastral_code <= 0:
            raise exceptions.ValidationError(_('The code must be a ' +
                                               'positive value.'))

    @api.model
    def create(self, vals):
        name_no_blanks = vals['name'].strip()
        cadastral_code_no_blanks = vals['cadastral_code'].strip()
        if len(cadastral_code_no_blanks) < 2:
            cadastral_code_no_blanks = '0' + cadastral_code_no_blanks
        if name_no_blanks != vals['name']:
            vals.update({'name': name_no_blanks})
        if cadastral_code_no_blanks != vals['cadastral_code']:
            vals.update({'cadastral_code': cadastral_code_no_blanks})
        return super(WuaRegionState, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            name_no_blanks = vals['name'].strip()
            if name_no_blanks != vals['name']:
                vals.update({'name': name_no_blanks})
        if 'cadastral_code' in vals:
            cadastral_code_no_blanks = vals['cadastral_code'].strip()
            if len(cadastral_code_no_blanks) < 2:
                cadastral_code_no_blanks = '0' + cadastral_code_no_blanks
            if cadastral_code_no_blanks != vals['cadastral_code']:
                vals.update({'cadastral_code': cadastral_code_no_blanks})
        return super(WuaRegionState, self).write(vals)


class WuaRegionStateCounty(models.Model):
    _name = 'wua.region.state.county'
    _description = 'County'
    _order = 'cadastral_state_county_code'

    name = fields.Char(
        string='County Name',
        size=50,
        required=True,
        index=True)

    cadastral_code = fields.Char(
        string='County Code',
        size=3,
        help='Three digits of the official cadastral code.',
        required=True)

    state_id = fields.Many2one(
        string='State',
        comodel_name='wua.region.state',
        required=True,
        ondelete='restrict')

    cadastral_state_code = fields.Char(
        string='Cadastral State Code',
        related='state_id.cadastral_code',
        readonly=True)

    cadastral_state_county_code = fields.Char(
        string='Cadastral State+County Code',
        help='Cadastral State Code with Cadastral County Code',
        required=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing County Name.'),
        ('unique_cadastral_state_county_code',
         'UNIQUE (cadastral_state_county_code)',
         'Existing Cadastral State+County Code.'),
        ]

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty County Name.'))

    @api.constrains('cadastral_code')
    def _check_cadastral_code(self):
        cadastral_code_no_blanks = self.cadastral_code.strip()
        if cadastral_code_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Cadastral Code.'))
        try:
            proposed_cadastral_code = int(cadastral_code_no_blanks)
        except:
            proposed_cadastral_code = 0
        if proposed_cadastral_code <= 0:
            raise exceptions.ValidationError(_('The code must be a ' +
                                               'positive value.'))

    @api.onchange('cadastral_code', 'state_id')
    def _onchange_cadastral_code_state_id(self):
        if self.cadastral_state_code and self.cadastral_code:
            self.cadastral_state_county_code = \
                self.cadastral_state_code + \
                str(self.cadastral_code).zfill(3)

    @api.model
    def create(self, vals):
        name_no_blanks = vals['name'].strip()
        cadastral_code_no_blanks = vals['cadastral_code'].strip()
        if len(cadastral_code_no_blanks) < 3:
            if len(cadastral_code_no_blanks) < 2:
                cadastral_code_no_blanks = '00' + cadastral_code_no_blanks
            else:
                cadastral_code_no_blanks = '0' + cadastral_code_no_blanks
        if name_no_blanks != vals['name']:
            vals.update({'name': name_no_blanks})
        if cadastral_code_no_blanks != vals['cadastral_code']:
            vals.update({'cadastral_code': cadastral_code_no_blanks})
        return super(WuaRegionStateCounty, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            name_no_blanks = vals['name'].strip()
            if name_no_blanks != vals['name']:
                vals.update({'name': name_no_blanks})
        if 'cadastral_code' in vals:
            cadastral_code_no_blanks = vals['cadastral_code'].strip()
            if len(cadastral_code_no_blanks) < 3:
                if len(cadastral_code_no_blanks) < 2:
                    cadastral_code_no_blanks = '00' + cadastral_code_no_blanks
                else:
                    cadastral_code_no_blanks = '0' + cadastral_code_no_blanks
            if cadastral_code_no_blanks != vals['cadastral_code']:
                vals.update({'cadastral_code': cadastral_code_no_blanks})
        return super(WuaRegionStateCounty, self).write(vals)
