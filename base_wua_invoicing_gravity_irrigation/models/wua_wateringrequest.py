# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'
    _description = 'Entity (watering request)'

    CONFIG_KEY_SET_PRODUCT = (
        'base_wua_invoicing_gravity_irrigation.'
        'default_set_product_id_for_wateringrequest')
    CONFIG_KEY_GRAVITY_PRODUCT = (
        'base_wua_invoicing_gravity_irrigation.default_gravity_product_id')

    # Size of field "name".
    MAX_SIZE_PARTNER_CODE = 6
    MAX_WATERINGREQUEST_SUFFIX = 3
    # Last + 1 for '-' before suffix
    MAX_SIZE_NAME = 11 + MAX_SIZE_PARTNER_CODE + MAX_WATERINGREQUEST_SUFFIX + 1

    @api.model_cr
    def init(self):
        default_product = self._default_product_id()
        if default_product:
            wateringrequests_no_watertype = \
                self.env['wua.wateringrequest'].search(
                    [('product_id', '=', False)])
            if wateringrequests_no_watertype:
                vals = {
                    'product_id': default_product,
                    }
                wateringrequests_no_watertype.write(vals)

    def _default_product_id(self):
        resp = None
        config = self.env['ir.config_parameter'].sudo()
        set_product = config.get_param(self.CONFIG_KEY_SET_PRODUCT)
        if set_product and set_product.lower() == 'true':
            product_id_str = config.get_param(self.CONFIG_KEY_GRAVITY_PRODUCT)
            if product_id_str:
                try:
                    resp = int(product_id_str)
                except (TypeError, ValueError):
                    resp = None
            if resp is None:
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
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')

    @api.depends('wateringperiod_id', 'wateringperiod_id.name',
                 'partner_id', 'product_id')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.wateringperiod_id and record.partner_id and \
                    record.product_id:
                # Default name
                name = record.wateringperiod_id.name + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
                wua_wateringrequest = self.env['wua.wateringrequest']
                wateringrequests = wua_wateringrequest.search(
                    [('wateringperiod_id', '=', record.wateringperiod_id.id),
                     ('partner_id', '=', record.partner_id.id),
                     ('id', '!=', record.id)])
                if (len(wateringrequests) > 0):
                    wrs_with_product = wua_wateringrequest.search(
                        [('product_id', '=', record.product_id.id),
                         ('wateringperiod_id', '=',
                            record.wateringperiod_id.id),
                         ('partner_id', '=', record.partner_id.id),
                         ('id', '!=', record.id)])
                    # If not wateringrequest with the same product_id
                    # Add suffix
                    if (len(wrs_with_product) == 0):
                        suffix = 1
                        name_temp = name + '-' + str(suffix).zfill(
                            self.MAX_WATERINGREQUEST_SUFFIX)
                        # Try with suffix 001 and keep iterating until no new
                        # one appear
                        while len(wua_wateringrequest.search(
                                [('name', '=', name_temp)])) > 0:
                            suffix += 1
                            name_temp = name + '-' + str(suffix).zfill(
                                self.MAX_WATERINGREQUEST_SUFFIX)
                        name = name_temp
            record.name = name

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.wateringperiod_id and record.partner_id and \
                    record.product_id:
                initial_date_str = self.env['wua.parcel'].\
                    transform_date_to_locale(
                        record.wateringperiod_id.initial_date)
                end_date_str = self.env['wua.parcel'].\
                    transform_date_to_locale(
                        record.wateringperiod_id.end_date)
                partner_name = record.partner_id.name + ' ' + \
                    '[' + str(record.partner_id.partner_code) + ']'
                name = initial_date_str + ' - ' + end_date_str + ' - ' + \
                    partner_name + ' - ' + record.product_id.name
            result.append((record.id, name))
        return result
