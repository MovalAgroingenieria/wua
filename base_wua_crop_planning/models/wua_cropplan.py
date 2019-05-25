# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCropplan(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.cropplan'
    _description = 'Crop Plan'
    _order = 'name'

    # Size of field "name".
    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_NAME = 22 + MAX_SIZE_PARTNER_CODE

    def _default_agriculturalseason_id(self):
        resp = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        if active_agriculturalseasons:
            resp = active_agriculturalseasons[0].id
        return resp

    def _default_partner_id(self):
        resp = 0
        partners = self.env['res.partner']
        user = self.env.user
        if not user.has_group('base_wua.group_wua_user'):
            partner = partners.browse(user.partner_id.id)
            if partner.is_wua_partner:
                resp = partner.id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        readonly=True,
        default=_default_agriculturalseason_id)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_partner_id)

    name = fields.Char(
        string='Crop Plan',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    request_date = fields.Date(
        string='Request Date',
        required=True,
        index=True,
        default=lambda self: fields.datetime.now())

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        required=True,
        index=True,
        readonly=True,
        default=lambda self: self.env.user,)

    enrolledsubparcel_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='cropplan_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Crop Plan.'),
        ]

    @api.depends('agriculturalseason_id', 'partner_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.agriculturalseason_id and record.partner_id:
                value = record.agriculturalseason_id.initial_date + '/' + \
                    record.agriculturalseason_id.end_date + '/' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = value
