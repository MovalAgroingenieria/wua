# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _in_create = False

    @api.model_cr
    def init(self):
        partners_updated_in_remotecontrol = self.env['res.partner'].search(
            [('is_wua_partner', '=', True),
             ('updated_in_remotecontrol', '=', True)])
        if not partners_updated_in_remotecontrol:
            partners = self.env['res.partner'].search(
                [('is_wua_partner', '=', True)])
            partners.write({
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
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & can_be_sent_partners_census

    @api.model
    def create(self, vals):
        self.__class__._in_create = True
        new_partner = super(ResPartner, self).create(vals)
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'automatic_census_synchronization')
        if (enable_remotecontrol and can_be_sent_partners_census and
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
                data = self.populate_data_for_send_new_partner(vals)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.send_new_partner(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Updating remote control for '
                                       'partner (new)')
                    suffix_message = 'OK'
                    if synchronized_remotecontrol:
                        self.env['res.partner'].browse(new_partner.id).\
                            updated_in_remotecontrol = True
                    else:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(new_partner.partner_code) + '... ' +
                                 suffix_message)
        self.__class__._in_create = False
        return new_partner

    @api.multi
    def write(self, vals):
        resp = super(ResPartner, self).write(vals)
        if (self.__class__._in_create or len(self) != 1):
            return resp
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'automatic_census_synchronization')
        if (enable_remotecontrol and can_be_sent_partners_census and
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
                data = self.populate_data_for_update_partner(self)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.update_partner(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Updating remote control for '
                                       'partner (existing)')
                    suffix_message = 'OK'
                    if not synchronized_remotecontrol:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(self.partner_code) + '... ' +
                                 suffix_message)
        return resp

    @api.multi
    def unlink(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'automatic_census_synchronization')
        if (enable_remotecontrol and can_be_sent_partners_census and
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
                    data = self.populate_data_for_delete_partner(record)
                    if data:
                        synchronized_remotecontrol, error_message = \
                            self.delete_partner(
                                url_remotecontrol_rest,
                                url_remotecontrol_rest_username,
                                url_remotecontrol_rest_password,
                                data)
                        prefix_message = _('Deleting remote control for '
                                           'partner ')
                        suffix_message = 'OK'
                        if not synchronized_remotecontrol:
                            if not error_message:
                                error_message = \
                                    _('Update error in remote control')
                            suffix_message = error_message
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info(prefix_message + ' ' +
                                     str(self.partner_code) + '... ' +
                                     suffix_message)
        return super(ResPartner, self).unlink()

    # Hook
    def populate_data_for_send_new_partner(self, vals):
        return None

    # Hook
    def send_new_partner(self, url_remotecontrol_rest,
                         url_remotecontrol_rest_username,
                         url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def populate_data_for_update_partner(self, vals):
        return None

    # Hook
    def update_partner(self, url_remotecontrol_rest,
                       url_remotecontrol_rest_username,
                       url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def populate_data_for_delete_partner(self, vals):
        return None

    # Hook
    def delete_partner(self, url_remotecontrol_rest,
                       url_remotecontrol_rest_username,
                       url_remotecontrol_rest_password, data):
        return False, ''

    @api.multi
    def do_synchronization_partner(self):
        self.ensure_one()
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        if (enable_remotecontrol and can_be_sent_partners_census):
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
                data = self.populate_data_for_update_partner(self)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.synchronize_partner(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Synchronizing remote control for '
                                       'partner')
                    suffix_message = 'OK'
                    if not synchronized_remotecontrol:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(self.partner_code) + '... ' +
                                 suffix_message)
                    if not synchronized_remotecontrol:
                        raise exceptions.UserError(_('ERROR ') + ':\n\n' +
                                                   suffix_message)
                    self.updated_in_remotecontrol = True

    def do_synchronization_partners(self, active_partners,
                                    show_message=False):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        if (enable_remotecontrol and can_be_sent_partners_census):
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
                partners = self.env['res.partner'].browse(active_partners)
                if not partners:
                    return False
                list_of_data = []
                for partner in partners:
                    data = self.populate_data_for_update_partner(partner)
                    list_of_data.append(data)
                if not list_of_data:
                    return False
                partners_ok, partners_not_ok = \
                    self.synchronize_partners(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password,
                        list_of_data)
                if not partners_ok and not partners_not_ok:
                    return False
                _logger = logging.getLogger(self.__class__.__name__)
                prefix_message = _('Synchronizing remote control for '
                                   'partners')
                suffix_message = 'OK'
                if partners_ok:
                    partners_ok_str = ''
                    for partner_code in partners_ok:
                        partners_ok_str = partners_ok_str + ', ' + \
                            str(partner_code)
                    partners_ok_str = partners_ok_str[2:]
                    _logger.info(prefix_message + ': ' +
                                 partners_ok_str + '... ' +
                                 suffix_message)
                if partners_not_ok:
                    suffix_message = _('Update error in remote control')
                    partners_not_ok_str = ''
                    for partner_code in partners_not_ok:
                        partners_not_ok_str = partners_not_ok_str + ', ' + \
                            str(partner_code)
                    partners_not_ok_str = partners_not_ok_str[2:]
                    _logger.info(prefix_message + ': ' +
                                 partners_not_ok_str + '... ' +
                                 suffix_message)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
            else:
                return False

    def do_synchronization_all_partners(self, show_message=False):
        partner_ids = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)]).ids
        if partner_ids:
            self.do_synchronization_partners(partner_ids, show_message)
        if not show_message:
            return True

    # Hook
    def synchronize_partner(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data):
        return False, ''

    # Hook
    def synchronize_partners(self, url_remotecontrol_rest,
                             url_remotecontrol_rest_username,
                             url_remotecontrol_rest_password, list_of_data):
        return False, ''
