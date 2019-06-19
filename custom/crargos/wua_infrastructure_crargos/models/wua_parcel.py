# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'
    _description = 'Parcel of a WUA with irrigation infrastructure ' \
                   '(C.R.Argos)'

    def test_other_slave_data(self, vals):
        super(WuaParcel, self).test_other_slave_data(vals)
        if ('subparcel_ids' in vals):
            correct_idbancals_no_repeat = \
                self.idbancals_no_repeat(
                    vals['subparcel_ids'])
            if not correct_idbancals_no_repeat:
                raise exceptions.UserError(_('There are repeated idbancal.'))
            idbancals_in_another_parcel = \
                self.idbancals_in_another_parcel(
                    vals['subparcel_ids'])
            if idbancals_in_another_parcel:
                raise exceptions.UserError(_('There are some idbancal '
                                             'in anoter parcel.'))

    def idbancals_no_repeat(self, subparcel_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if subparcel_oper == 4 or (subparcel_oper == 1 and
               'id_bancal' not in subparcel_vals):
                unchanged_ids.append(subparcel_id)
            if subparcel_oper == 0 or (subparcel_oper == 1 and
               'id_bancal' in subparcel_vals):
                implied_ids.append(subparcel_vals['id_bancal'])
        if len(unchanged_ids) > 0:
            filtered_subparcels = \
                self.env['wua.parcel.subparcel'].search(
                    [('id', 'in', unchanged_ids)])
            for subparcel in filtered_subparcels:
                implied_ids.append(subparcel.id_bancal)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        len_of_implied_ids_original = len(implied_ids)
        if len_of_implied_ids_original > 0:
            implied_ids = list(set(implied_ids))
            len_of_implied_ids_no_repeat = len(implied_ids)
            resp = len_of_implied_ids_original == len_of_implied_ids_no_repeat
        return resp

    def idbancals_in_another_parcel(self, subparcel_ids):
        implied_ids = []
        unchanged_ids = []
        parcel_id = None
        if self.id:
            parcel_id = self.id
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if subparcel_oper == 4 or (subparcel_oper == 1 and
               'id_bancal' not in subparcel_vals):
                unchanged_ids.append(subparcel_id)
            if subparcel_oper == 0 or (subparcel_oper == 1 and
               'id_bancal' in subparcel_vals):
                implied_ids.append(subparcel_vals['id_bancal'])
            if parcel_id is None and 'parcel_id' in subparcel_vals:
                parcel_id = subparcel_vals['parcel_id']
        if len(unchanged_ids) > 0:
            filtered_subparcels = \
                self.env['wua.parcel.subparcel'].search(
                    [('id', 'in', unchanged_ids)])
            for subparcel in filtered_subparcels:
                implied_ids.append(subparcel.id_bancal)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        other_subparcels = self.env['wua.parcel.subparcel'].search(
            [('id_bancal', 'in', implied_ids),
             ('parcel_id', '!=', parcel_id)])
        resp = len(other_subparcels) > 0
        return resp


class WuaParcelSubparcel(models.Model):
    _inherit = 'wua.parcel.subparcel'
    _description = 'Subparcel of a parcel with irrigation infrastructure ' \
                   '(C.R.Argos)'

    id_bancal = fields.Integer(
        string='IdBancal',
        default=0)

    _sql_constraints = [
        ('valid_id_bancal',
         'CHECK (id_bancal >= 0)',
         'The IdBancal must be a value zero or positive.')]

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            parcel_code = record.parcel_id.name
            name = parcel_code + ' [' + str(record.pos) + ']'
            id_bancal = record.id_bancal
            if id_bancal > 0:
                name = str(id_bancal) + ' ' + name
            result.append((record.id, name))
        return result


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    rurallocation = fields.Char(
        compute='_get_rurallocation_id',
        string="Rural Location",
        size=255)
    pressurized_irrigation_right = fields.Boolean(
        compute='_get_pressurized_irrigation_right',
        string="Irrigation Right")
    gravityfed_irrigation_right = fields.Boolean(
        compute='_get_gravityfed_irrigation_right',
        string="Gravityfed Right")

    @api.multi
    def _get_rurallocation_id(self):
        for record in self:
            record.rurallocation = record.parcel_id.rurallocation_id.name

    @api.multi
    def _get_pressurized_irrigation_right(self):
        for record in self:
            record.pressurized_irrigation_right = \
                record.parcel_id.pressurized_irrigation_right

    @api.multi
    def _get_gravityfed_irrigation_right(self):
        for record in self:
            record.gravityfed_irrigation_right = \
                record.parcel_id.gravityfed_irrigation_right
