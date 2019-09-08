# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


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
                data = self.populate_data_for_send_new_parcel(vals)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.send_new_parcel(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Remote Control: Updating remote '
                                       'control for parcel (new)')
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

    @api.multi
    def write(self, vals):
        resp = super(WuaParcel, self).write(vals)
        if (self.__class__._in_create or len(self) != 1):
            return resp
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
                data = self.populate_data_for_update_parcel(self)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.update_parcel(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Remote Control: Updating remote '
                                       'control for parcel (existing)')
                    suffix_message = 'OK'
                    if not synchronized_remotecontrol:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(self.name) + '... ' +
                                 suffix_message)
        return resp

    @api.multi
    def unlink(self):
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
                for record in self:
                    data = self.populate_data_for_delete_parcel(record)
                    if data:
                        synchronized_remotecontrol, error_message = \
                            self.delete_parcel(
                                url_remotecontrol_rest,
                                url_remotecontrol_rest_username,
                                url_remotecontrol_rest_password,
                                data)
                        prefix_message = _('Remote Control: Deleting remote '
                                           'control for parcel ')
                        suffix_message = 'OK'
                        if not synchronized_remotecontrol:
                            if not error_message:
                                error_message = \
                                    _('Update error in remote control')
                            suffix_message = error_message
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info(prefix_message + ' ' +
                                     str(record.name) + '... ' +
                                     suffix_message)
        return super(WuaParcel, self).unlink()

    # Hook
    def populate_data_for_send_new_parcel(self, vals):
        return None

    # Hook
    def send_new_parcel(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def populate_data_for_update_parcel(self, vals):
        return None

    # Hook
    def update_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def populate_data_for_delete_parcel(self, parcel):
        return None

    # Hook
    def delete_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password, data):
        return False, ''

    @api.multi
    def do_synchronization_parcel(self):
        self.ensure_one()
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_parcels_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_parcels_census')
        if (enable_remotecontrol and can_be_sent_parcels_census):
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
                data = self.populate_data_for_update_parcel(self)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.synchronize_parcel(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Remote Control: Synchronizing '
                                       'remote control for parcel')
                    suffix_message = 'OK'
                    if not synchronized_remotecontrol:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(self.name) + '... ' +
                                 suffix_message)
                    if not synchronized_remotecontrol:
                        raise exceptions.UserError(_('ERROR ') + ':\n\n' +
                                                   suffix_message)
                    self.updated_in_remotecontrol = True

    def do_synchronization_parcels(self, active_parcels,
                                   show_message=False):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_parcels_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_parcels_census')
        if (enable_remotecontrol and can_be_sent_parcels_census):
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
                parcels = self.env['wua.parcel'].browse(active_parcels)
                if parcels:
                    list_of_data = []
                    for parcel in parcels:
                        data = self.populate_data_for_update_parcel(parcel)
                        list_of_data.append(data)
                    if list_of_data:
                        parcels_ok, parcels_not_ok = \
                            self.synchronize_parcels(
                                url_remotecontrol_rest,
                                url_remotecontrol_rest_username,
                                url_remotecontrol_rest_password,
                                list_of_data)
                        if parcels_ok or parcels_not_ok:
                            _logger = logging.getLogger(
                                self.__class__.__name__)
                            prefix_message = _('Remote Control: Synchronizing '
                                               'remote control for parcels')
                            suffix_message = 'OK'
                            if parcels_ok:
                                parcels_ok_str = ''
                                for name in parcels_ok:
                                    self.env['wua.parcel'].search(
                                        [('name', '=', name)]).\
                                        updated_in_remotecontrol = True
                                    parcels_ok_str = parcels_ok_str + ', ' + \
                                        str(name)
                                parcels_ok_str = parcels_ok_str[2:]
                                _logger.info(prefix_message + ': ' +
                                             parcels_ok_str + '... ' +
                                             suffix_message)
                            if parcels_not_ok:
                                suffix_message = _('Update error in remote '
                                                   'control')
                                parcels_not_ok_str = ''
                                for name in parcels_not_ok:
                                    parcels_not_ok_str = \
                                        parcels_not_ok_str + ', ' + \
                                        str(name)
                                parcels_not_ok_str = parcels_not_ok_str[2:]
                                _logger.info(prefix_message + ': ' +
                                             parcels_not_ok_str + '... ' +
                                             suffix_message)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))

    def do_synchronization_all_parcels(self, show_message=False):
        parcel_ids = self.env['wua.parcel'].search([]).ids
        if parcel_ids:
            self.do_synchronization_parcels(parcel_ids, show_message)
        if not show_message:
            return True

    # Hook
    def synchronize_parcel(self, url_remotecontrol_rest,
                           url_remotecontrol_rest_username,
                           url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def synchronize_parcels(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, list_of_data):
        return None, None
