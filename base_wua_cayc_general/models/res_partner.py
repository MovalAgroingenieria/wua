# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math
from lxml import etree
from odoo import models, fields, _, exceptions, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_primary = fields.Boolean(
        string='Is primary',
        compute='_compute_is_primary',
        store=True,
        index=True,
    )

    wuabase_id = fields.Many2one(
        string='WUA Base',
        comodel_name='wua.wuabase',
        compute='_compute_wuabase_id',
        store=True,
        index=True,
    )

    partner_type = fields.Selection([
        ('01_WUA', 'Water User Association'),
        ('02_IND', 'Industry'),
        ('03_WSP', 'Water Supply'),
        ('04_HEL', 'Hydroelectric Producer'),
    ], string='Partner Type',
        index=True,
    )

    concession_as_volume = fields.Float(
        string='Concession As Volume',
        digits=(32, 4),
        default=0,
    )

    concession_as_power = fields.Float(
        string='Concession As Power',
        digits=(32, 4),
        default=0,
    )

    _sql_constraints = [
        ('valid_concession_as_volume',
         'CHECK (concession_as_volume >= 0)',
         'The concession as volume must be a value zero or positive.'),
        ('valid_concession_as_power',
         'CHECK (concession_as_power >= 0)',
         'The concession as power must be a value zero or positive.'),
    ]

    @api.constrains('partner_code')
    def _check_partner_code(self):
        super(ResPartner, self)._check_partner_code()
        if ((self.env.context.get('wua') == '1' or self.is_wua_partner) and
                (not self.parent_id)):
            # Primary partenr
            if (self.partner_code > 9999 and self.partner_code % 10000 == 0):
                raise exceptions.ValidationError(
                    _('The secondary partner code must not end at 0.'))
            else:
                # Primary partner
                code_to_search = str(self.partner_code).zfill(3)
                if (self.partner_code > 10000):
                    # Secondary partner
                    code_to_search = str(self.partner_code / 10000).zfill(3)
                wuabase = self.env['wua.wuabase'].search(
                    [('name', '=', code_to_search)])
                if (not wuabase or len(wuabase) < 1):
                    raise exceptions.ValidationError(
                        _('The WUA Base code does not exists.'))

    @api.constrains('is_primary', 'partner_type')
    def check_partner_type(self):
        for record in self:
            if (record.is_primary and not record.partner_type):
                raise exceptions.ValidationError(
                    _('A primary partner must have a valid partner type .'))

    @api.depends('partner_code')
    def _compute_is_primary(self):
        for record in self:
            is_primary = False
            if (record.partner_code > 0 and record.partner_code < 10000):
                is_primary = True
            record.is_primary = is_primary

    @api.depends('partner_code')
    def _compute_wuabase_id(self):
        for record in self:
            wuabase_id = None
            code_to_search = False
            if (record.partner_code < 10000):
                code_to_search = str(record.partner_code).zfill(3)
            elif (record.partner_code >= 10000):
                code_to_search = str(record.partner_code / 10000).zfill(3)
            # IDEA: self.env.ref?
            if (code_to_search):
                wuabase_id = self.env['wua.wuabase'].search(
                    [('name', '=', code_to_search)])
            record.wuabase_id = wuabase_id

    @api.depends('parcel_owner_number_votes', 'parcel_owner_area_hec_votes',
                 'is_primary', 'partner_type',
                 'concession_as_volume', 'concession_as_power',)
    def _compute_number_of_votes(self):
        if len(self) != 1:
            return
        if not self.is_primary:
            self.number_of_votes = 0
        elif self.partner_type != '01_WUA':
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type')
            votes = 0
            divider = 1
            if (self.partner_type in ['02_IND', '03_WSP']):
                concession_value = self.concession_as_volume
                if self.partner_type == '02_IND':
                    divider = 1000
                else:
                    divider = 4000
            else:
                concession_value = self.concession_as_power
                divider = 2.5
            area_for_votes = (concession_value / divider) * 10000
            if polling_system_type == 2 or polling_system_type == 3:
                if polling_system_type == 2:
                    polling_system_interval = self.env['ir.values'].\
                        get_default('wua.configuration',
                                    'polling_system_interval')
                    if polling_system_interval > 0:
                        polling_system_rounding_type = \
                            self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_rounding_type')
                        calc_votes =\
                            area_for_votes / float(polling_system_interval)
                        if polling_system_rounding_type == 0:
                            votes = math.ceil(calc_votes)
                        else:
                            votes = math.floor(calc_votes)
                if polling_system_type == 3:
                    polling_system_intervals = self.env['ir.values'].\
                        get_default('wua.configuration',
                                    'polling_system_intervals')
                    if polling_system_intervals:
                        votes = self.assign_votes_by_range(
                            area_for_votes, polling_system_intervals)
            self.number_of_votes = votes
        else:
            super(ResPartner, self)._compute_number_of_votes()

    def clear_vals_for_che_partner(self, vals):
        vals['customer'] = False
        vals['partner_type'] = None
        vals['concession_as_volume'] = 0.0
        vals['concession_as_power'] = 0.0

    @api.model
    def create(self, vals):
        if ('partner_code' in vals and vals['partner_code'] > 9999):
            self.clear_vals_for_che_partner(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('partner_code' in vals and vals['partner_code'] > 9999):
            self.clear_vals_for_che_partner(vals)
        return super(ResPartner, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        result = super(ResPartner, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree' and self.env.context.get(
                'is_primary_partner', False):
            doc = etree.XML(result['arch'])
            hide_fields = [
                'parcel_owner_number',
                'parcel_owner_area',
                'parcel_lessee_number',
                'parcel_lessee_area',
            ]
            for field in hide_fields:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            result['arch'] = etree.tostring(doc)
        return result
