# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from time import time
from odoo import models, fields, api


class ResNotificationsetType(models.Model):
    _inherit = 'res.notificationset.type'

    include_partner_if_wua = fields.Boolean(
        string='Include WUA partners',
        default=True,)

    include_partner_if_customer = fields.Boolean(
        default=False,)

    include_partner_if_supplier = fields.Boolean(
        default=False,)

    attach_report_id = fields.Many2one(
        string='Report to Attach',
        comodel_name='ir.actions.report.xml',
        domain=[('model', '=', 'res.partner')],
        index=True,
        ondelete='restrict',)

    def _get_a_partner(self):
        resp = None
        conditions = []
        if (not self.include_partner_all):
            if self.include_partner_if_wua:
                conditions = [('is_wua_partner', '=', True),
                              ('parent_id', '=', False),
                              ('partner_share', '=', True)]
            else:
                if self.include_partner_if_customer:
                    conditions = [('is_wua_partner', '=', False),
                                  ('customer', '=', True),
                                  ('parent_id', '=', False),
                                  ('partner_share', '=', True)]
                else:
                    conditions = [('is_wua_partner', '=', False),
                                  ('supplier', '=', True),
                                  ('parent_id', '=', False),
                                  ('partner_share', '=', True)]
        partners = self.env['res.partner'].search(conditions, order='name')
        if partners:
            number_of_partners = len(partners)
            epoch_time = int(time())
            partner_to_select = epoch_time % number_of_partners
            resp = partners[partner_to_select]
        return resp

    @api.constrains('include_partner_if_wua',
                    'include_partner_if_customer',
                    'include_partner_if_supplier',
                    'include_partner_all')
    def _check_include_partner_client_supplier(self):
        super(ResNotificationsetType,
              self)._check_include_partner_client_supplier()

    def _is_marked_an_option(self, record):
        resp = super(ResNotificationsetType,
                     self)._is_marked_an_option(record)
        if not resp:
            resp = record.include_partner_if_wua
        return resp

    def _option_marked_if_all(self, record):
        resp = super(ResNotificationsetType,
                     self)._option_marked_if_all(record)
        if not resp:
            resp = record.include_partner_all and record.include_partner_if_wua
        return resp
