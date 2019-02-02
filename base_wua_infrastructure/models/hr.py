# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee of a WUA with irrigation infrastructure'

    is_irrigation_worker = fields.Boolean(
        string="Irrigation Worker",
        default=False)

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='employee_id')

    number_of_parcels = fields.Integer(
        string='Parcels',
        store=True,
        compute='_compute_number_of_parcels')

    @api.depends('parcel_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = len(record.parcel_ids)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(Employee, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_form(doc)
        if view_type == 'kanban':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_kanban(doc)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_search(doc)
        return res

    def fields_view_get_form(self, doc):
        # If the user is in 'base_wua.group_wua_user' group
        # (but he is not in 'base_wua.group_wua_manager' group),
        # then the 'is_irrigation_worker' field will not be editable.
        if (self.env.user.has_group('base_wua.group_wua_user') and
           not self.env.user.has_group('base_wua.group_wua_manager')):
            for node in doc.xpath(
                    "//field[@name='is_irrigation_worker']"):
                node.set('modifiers',
                         '{"readonly": true}')
        # Others.
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            for node in doc.xpath(
                    "//field[@name='is_irrigation_worker']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        return etree.tostring(doc)

    def fields_view_get_kanban(self, doc):
        # If the user is not in 'base_wua.group_wua_user',
        # then the 'is_irrigation_worker' and 'number_of_parcels' fields
        # will not be visibles.
        if not self.env.user.has_group('base_wua.group_wua_user'):
            for node in doc.xpath(
                    "//li[@t-if='record.is_irrigation_worker.raw_value']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        return etree.tostring(doc)

    def fields_view_get_search(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            for node in doc.xpath(
                    "//filter[@name='is_irrigation_worker']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        return etree.tostring(doc)
