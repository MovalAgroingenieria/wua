# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    _in_create = False

    @api.model_cr
    def init(self):
        parcels_updated_in_remotecontrol = self.env['wua.parcel'].search(
            [('updated_in_remotecontrol', '=', True)])
        if not parcels_updated_in_remotecontrol:
            parcels = self.env['wua.parcel'].search([])
            parcels.write({
                'updated_in_remotecontrol': False,
                })

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    updated_in_remotecontrol = fields.Boolean(
        string='Updated in Remote Control',
        default=False)

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_parcels_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_parcels_census')
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & can_be_sent_parcels_census

    @api.model
    def create(self, vals):
        self.__class__._in_create = True
        new_parcel = super(WuaParcel, self).create(vals)
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_parcels_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_parcels_census')
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'automatic_census_synchronization')
        if (enable_remotecontrol and can_be_sent_parcels_census and
           automatic_census_synchronization):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'url_remotecontrol_rest')
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username')
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password')
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
               url_remotecontrol_rest_password):
                # Provisional
                data = self.populate_data_for_send_new_parcel(vals)
                if data:
                    # Provisional
                    print data
                    synchronized_remotecontrol, error_message = \
                        self.send_new_parcel(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Updating remote control for '
                                       'parcel (new)')
                    suffix_message = 'OK'
                    if synchronized_remotecontrol:
                        self.env['wua.parcel'].browse(new_parcel.id).\
                            updated_in_remotecontrol = True
                    else:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 new_parcel.name + '... ' +
                                 suffix_message)
        self.__class__._in_create = False
        return new_parcel

    # Hook
    def populate_data_for_send_new_parcel(self, vals):
        return None

    # Hook
    def send_new_parcel(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data):
        return False, ''
