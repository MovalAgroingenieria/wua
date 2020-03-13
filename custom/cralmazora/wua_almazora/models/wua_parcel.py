# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'
    _description = 'Entity (parcel of Almassora)'

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        index=True,
        store=True,
        compute='_compute_waterconnection_id',
        ondelete='restrict')

    gross_amount = fields.Float(
        string='Gross Amount',
        digits=(32, 2),
        compute='_compute_gross_amount')

    net_parcel_amount = fields.Float(
        string='Net for parcel',
        digits=(32, 2),
        compute='_compute_net_parcel_amount')

    net_worker_amount = fields.Float(
        string='Net for worker',
        digits=(32, 2),
        compute='_compute_net_worker_amount')

    @api.depends('irrigationpoint_ids')
    def _compute_waterconnection_id(self):
        for record in self:
            irrigation_points = record.irrigationpoint_ids
            waterconnection_id = None
            if len(irrigation_points) > 0:
                for irrigation_point in irrigation_points:
                    if irrigation_point.type == 'WC':
                        waterconnection_id = \
                            irrigation_point.waterconnection_id
                        break
            record.waterconnection_id = waterconnection_id

    @api.multi
    def _compute_gross_amount(self):
        gross_price = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'gross_price')
        if not gross_price:
            gross_price = 0
        for record in self:
            if record.with_irrigation_worker:
                record.gross_amount = gross_price * record.area_irrigation
            else:
                record.gross_amount = 0

    @api.multi
    def _compute_net_parcel_amount(self):
        gross_price = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'gross_price')
        if not gross_price:
            gross_price = 0
        net_coefficient_parcels = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'net_coefficient_parcels')
        if not net_coefficient_parcels:
            net_coefficient_parcels = 0
        for record in self:
            if record.with_irrigation_worker:
                record.net_parcel_amount = gross_price * \
                    record.area_official * net_coefficient_parcels
            else:
                record.net_parcel_amount = 0

    @api.depends('gross_amount', 'net_parcel_amount')
    def _compute_net_worker_amount(self):
        for record in self:
            record.net_worker_amount = \
                record.gross_amount - record.net_parcel_amount

    def create_subparcel_unique(self, parcel):
        irrigationgates = self.env['wua.irrigationgate']
        filtered_irrigationgates = irrigationgates.search(
            [('name', '=', parcel.name)])
        if len(filtered_irrigationgates) == 1:
            irrigationgate = filtered_irrigationgates[0]
            subparcels = self.env['wua.parcel.subparcel']
            vals = {'subparcel_code': parcel.name + '-' +
                    '1'.zfill(self.SIZE_SUBPARCEL_SUFFIX),
                    'parcel_id': parcel.id,
                    'pos': 1,
                    'area_official': parcel.area_official,
                    'area_perc': 100,
                    'irrigationgate_id': irrigationgate.id,
                    'active': parcel.active}
            subparcels.create(vals)
        else:
            raise exceptions.UserError(_(
                'Each parcel must have a subparcel with an '
                'irrigation gate; in addition, the code of the '
                'irrigation gate must be equal to parcel code.'))

    def test_other_slave_data(self, vals):
        if ('subparcel_ids' in vals and
           len(vals['subparcel_ids']) > 0):
            parcel_code = ''
            if 'name' in vals:
                parcel_code = vals['name']
            irrigationgate_ok = self.irrigationgate_ok(
                vals['subparcel_ids'], parcel_code)
            if not irrigationgate_ok:
                raise exceptions.UserError(_(
                    'Each parcel must have a subparcel with an '
                    'irrigation gate; in addition, the code of the '
                    'irrigation gate must be equal to parcel code.'))
        if ('irrigationpointwc_ids' in vals and
           len(vals['irrigationpointwc_ids']) > 0):
            waterconnection_ok = self.waterconnection_ok(
                vals['irrigationpointwc_ids'])
            if not waterconnection_ok:
                raise exceptions.UserError(_(
                    'Each parcel can have a single water connection.'))

    def irrigationgate_ok(self, subparcel_ids, parcel_code):
        resp = True
        num_subparcels = 0
        current_subparcel_id = 0
        current_subparcel_vals = {}
        if parcel_code == '':
            parcel_code = self.name
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if (subparcel_oper == 0 or subparcel_oper == 1 or
               subparcel_oper == 4):
                num_subparcels = num_subparcels + 1
                current_subparcel_id = subparcel_id
                current_subparcel_vals = subparcel_vals
        if num_subparcels == 1:
            irrigationgate_id = 0
            if 'irrigationgate_id' in current_subparcel_vals:
                irrigationgate_id = \
                    current_subparcel_vals['irrigationgate_id']
            else:
                current_subparcel = self.env['wua.parcel.subparcel'].browse(
                    current_subparcel_id)
                if current_subparcel:
                    irrigationgate_id = current_subparcel.irrigationgate_id.id
            if irrigationgate_id == 0:
                resp = False
            else:
                irrigationgate = self.env['wua.irrigationgate'].browse(
                    irrigationgate_id)
                if irrigationgate:
                    if irrigationgate.name != parcel_code:
                        resp = False
                else:
                    resp = False
        else:
            resp = False
        return resp

    def waterconnection_ok(self, irrigationpointwc_ids):
        resp = True
        num_irrigationpointswc = 0
        for irrigationpointwc in irrigationpointwc_ids:
            irrigationpointwc_oper = irrigationpointwc[0]
            if (irrigationpointwc_oper == 0 or irrigationpointwc_oper == 1 or
               irrigationpointwc_oper == 4):
                num_irrigationpointswc = num_irrigationpointswc + 1
        if num_irrigationpointswc > 1:
            resp = False
        return resp

    # For report.
    def next_parcel_label(self, docs, i, field):
        value = None
        if i < len(docs):
            next_record = docs[i]
            if field == 'irrigationditch':
                value = next_record.irrigationditch_id.name
            if field == 'name':
                value = next_record.name
            if field == 'cadastralref':
                value = next_record.cadastral_reference
            if field == 'area':
                value = '{:0.2f}'.format(next_record.area_official)
            if field == 'grossamount':
                value = '{:0.2f}'.format(next_record.gross_amount)
        return value

    # For report.
    def get_area_measurement_name(self):
        area_measurement_name = _('ha')
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode('utf_8')
        return area_measurement_name

    # For report.
    def get_year(self):
        year = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'year')
        return year
