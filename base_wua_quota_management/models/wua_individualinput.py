# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api, _


class WuaIndividualinput(models.Model):
    _name = 'wua.individualinput'
    _description = 'Individual Input'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME

    def _default_agriculturalseason_id(self):
        resp = 0
        proposed_agriculturalseason_id = \
            self.env.context.get('agriculturalseason_id', False)
        if proposed_agriculturalseason_id:
            resp = proposed_agriculturalseason_id
        else:
            active_agriculturalseason = \
                (self.env['wua.agriculturalseason'].
                 get_active_agriculturalseason())
            if active_agriculturalseason:
                resp = active_agriculturalseason.id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict')

    event_time = fields.Datetime(
        string='Time',
        required=True,
        index=True)

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 4),
        default=0,
        required=True)

    is_negative = fields.Boolean(
        string='Is negative',
        store=True,
        compute='_compute_is_negative')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_quota_id')

    quota_name = fields.Char(
        string='Quota',
        size=MAX_SIZE_QUOTA_NAME,
        store=True,
        index=True,
        compute='_compute_quota_name')

    name = fields.Char(
        string='Individual Input',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    quota_initial_value = fields.Float(
        string='Initial Value',
        digits=(32, 4),
        compute='_compute_quota_initial_value')

    quota_accumulated_consumption = fields.Float(
        string='Consumption',
        digits=(32, 4),
        compute='_compute_quota_accumulated_consumption')

    quota_balance = fields.Float(
        string='Balance',
        digits=(32, 4),
        compute='_compute_quota_balance')

    quota_negative_balance = fields.Float(
        string='Balance',
        digits=(32, 4),
        compute='_compute_quota_negative_balance')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input.'),
        ('non_zero_volume', 'CHECK (volume <> 0)',
         'Zero is not a valid value for the volume field.'),
        ]

    @api.depends('volume')
    def _compute_is_negative(self):
        for record in self:
            is_negative = False
            if record.volume < 0:
                is_negative = True
            record.is_negative = is_negative

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('quotaperiod_id', 'superproduct_id', 'partner_id')
    def _compute_quota_id(self):
        for record in self:
            quota_id = None
            if (record.quotaperiod_id and record.superproduct_id and
               record.partner_id):
                filtered_quotas = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', record.quotaperiod_id.id),
                     ('superproduct_id', '=', record.superproduct_id.id),
                     ('partner_id', '=', record.partner_id.id)])
                if filtered_quotas:
                    quota_id = filtered_quotas[0]
            record.quota_id = quota_id

    @api.depends('quota_id', 'quota_id.name')
    def _compute_quota_name(self):
        for record in self:
            quota_name = ''
            if record.quota_id:
                quota_name = record.quota_id.name
            record.quota_name = quota_name

    @api.depends('quota_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.quota_name and record.event_time:
                name = record.quota_name + ' - ' + record.event_time
            record.name = name

    @api.multi
    def _compute_quota_initial_value(self):
        for record in self:
            quota_initial_value = 0
            if record.quota_id:
                quota_initial_value = record.quota_id.initial_value
            record.quota_initial_value = quota_initial_value

    @api.multi
    def _compute_quota_accumulated_consumption(self):
        for record in self:
            quota_accumulated_consumption = 0
            if record.quota_id:
                quota_accumulated_consumption = \
                    record.quota_id.accumulated_consumption
            record.quota_accumulated_consumption = \
                quota_accumulated_consumption

    @api.multi
    def _compute_quota_balance(self):
        for record in self:
            quota_balance = 0
            if record.quota_id:
                quota_balance = record.quota_id.balance
            record.quota_balance = quota_balance

    @api.multi
    def _compute_quota_negative_balance(self):
        # Auxiliary field for negative balances in red (form view).
        for record in self:
            record.quota_negative_balance = record.quota_balance

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIndividualinput, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if (view_type == 'form' and
           self.env.context.get('agriculturalseason_id', False)):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='agriculturalseason_id']"):
                node.set('readonly', '1')
                node.set('modifiers',
                         '{"readonly": true, "required": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_open_quota_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_quota_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Quotas'),
            'res_model': 'wua.quota',
            'res_id': self.quota_id.id,
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'flags': {'mode': 'readonly'}
            }
        return act_window
