# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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

    @api.constrains('partner_code')
    def _check_partner_code(self):
        super(ResPartner, self)._check_partner_code()
        if ((self.env.context.get('wua') == '1' or self.is_wua_partner) and
                (not self.parent_id)):
            # Primary partenr
            if (self.partner_code > 9999 and self.partner_code / 10000 == 0):
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

    @api.constrains('is_primary', 'partnerlink_ids')
    def check_primary_partnerlinks(self):
        for record in self:
            if (len(record.partnerlink_ids) > 0):
                if record.is_primary and len(record.partnerlink_ids.filtered(
                        lambda x: not x.parcel_id.is_primary)) > 0:
                    raise exceptions.ValidationError(
                        _('A primary partner cannot have a non primary '
                          'parcel.'))
                elif not record.is_primary and len(
                    record.partnerlink_ids.filtered(
                        lambda x: x.parcel_id.is_primary)) > 0:
                    raise exceptions.ValidationError(
                        _('A CHE partner cannot have a non CHE '
                          'parcel.'))

    @api.depends('partner_code')
    def _compute_is_primary(self):
        for record in self:
            is_primary = False
            if (record.partner_code < 10000):
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
