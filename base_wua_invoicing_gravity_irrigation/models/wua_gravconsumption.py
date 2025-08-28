# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'
    _description = 'Entity (gravity consumption)'

    # Size of field "name".
    MAX_SIZE_WATERINGPERIOD = 10
    MAX_SIZE_SUBPARCEL = 25
    MAX_SIZE_NUMBER = 2
    MAX_WATERINGREQUEST_SUFFIX = 3
    # Last +1 for '-' before suffix
    MAX_SIZE_NAME = MAX_SIZE_SUBPARCEL + MAX_SIZE_WATERINGPERIOD + \
        MAX_SIZE_NUMBER + 2 + MAX_WATERINGREQUEST_SUFFIX + 1

    def _default_product_id(self):
        resp = None
        default_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_gravity_product_id')
        if default_product_id:
            resp = default_product_id
        else:
            categ_08_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 8)], order='id')
            if len(categ_08_products) > 0:
                resp = categ_08_products[0].id
        return resp

    name = fields.Char(
        size=MAX_SIZE_NAME,)

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        ondelete='restrict')

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null')

    invoiced_consumption = fields.Boolean(
        string='Invoiced',
        default=False,
        required=True)

    wateringrequest_suffix = fields.Integer(
        string='Watering Request Suffix',
        store=True,
        default=0,
        compute='_compute_wateringrequest_suffix'
    )

    overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue')

    @api.multi
    def _compute_overdue(self):
        for record in self:
            overdue = False
            if record.parcel_id and record.parcel_id.overdue:
                overdue = True
            record.overdue = overdue

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(WuaGravconsumption, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy)
        for item in res:
            if 'invoiced_consumption' in item:
                if item['invoiced_consumption']:
                    item['invoiced_consumption'] = _('Invoiced')
                else:
                    item['invoiced_consumption'] = _('Not Invoiced')
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.wateringperiod_id.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.wateringperiod_id.end_date)
            subparcel_code = record.subparcel_id.subparcel_code
            name = initial_date_str + ' - ' + end_date_str + ' - ' + \
                subparcel_code
            if (record.wateringrequest_suffix > 0):
                name += ' - ' + str(record.wateringrequest_suffix).zfill(
                    self.MAX_WATERINGREQUEST_SUFFIX)
            result.append((record.id, name))
        return result

    @api.depends('subparcel_id', 'wateringperiod_id', 'number',
                 'wateringrequest_suffix')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.subparcel_id and record.wateringperiod_id:
                value = record.wateringperiod_id.name + '-' + \
                    record.subparcel_id.subparcel_code + '-' + \
                    str(record.number).zfill(
                        self.MAX_SIZE_NUMBER)
                if (record.wateringrequest_suffix > 0):
                    value += '-' + str(record.wateringrequest_suffix).zfill(
                        self.MAX_WATERINGREQUEST_SUFFIX)
            record.name = value

    @api.depends('wateringrequest_id', 'wateringrequest_id.name')
    def _compute_wateringrequest_suffix(self):
        for record in self:
            wateringrequest_suffix = 0
            if (record.wateringrequest_id and record.wateringrequest_id.name):
                # If the name length is the MAX, it means that has suffix
                if (len(record.wateringrequest_id.name) ==
                        record.wateringrequest_id.MAX_SIZE_NAME):
                    # Get Last MAX_WATERINGREQUEST_SUFFIX chars and transform
                    # to int
                    wateringrequest_suffix = int(
                        record.wateringrequest_id.name[
                            -record.wateringrequest_id.
                            MAX_WATERINGREQUEST_SUFFIX:]
                    )
            record.wateringrequest_suffix = wateringrequest_suffix
