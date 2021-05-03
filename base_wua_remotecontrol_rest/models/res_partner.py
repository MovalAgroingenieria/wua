# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _, tools


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _in_create_or_synchro = False
    # Populate on children
    _remotecontrol_partner_fields = []

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
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if can_be_sent_partners_census is None:
            can_be_sent_partners_census = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & can_be_sent_partners_census

    @api.model
    def create(self, vals):
        self.__class__._in_create_or_synchro = True
        new_partner = super(ResPartner, self).create(vals)
        if 'is_wua_partner' in vals and vals['is_wua_partner']:
            enable_remotecontrol = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'enable_remotecontrol')
            can_be_sent_partners_census = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'can_be_sent_partners_census')
            automatic_census_synchronization = \
                self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'automatic_census_synchronization')
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
                if (url_remotecontrol_rest and
                   url_remotecontrol_rest_username and
                   url_remotecontrol_rest_password):
                    data = self.populate_data_for_send_new_partner(vals)
                    if data:
                        synchronized_remotecontrol, error_message = \
                            self.send_new_partner(
                                url_remotecontrol_rest,
                                url_remotecontrol_rest_username,
                                url_remotecontrol_rest_password,
                                data)
                        prefix_message = _('Remote Control: Updating remote '
                                           'control for partner (new)')
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
        self.__class__._in_create_or_synchro = False
        return new_partner

    @api.multi
    def write(self, vals):
        resp = super(ResPartner, self).write(vals)
        some_remotecontrol_key = False
        all_vals = vals.keys()
        # Intersect the vals written and the possible keys taht will trigger
        # the update (_remotecontrol_partner_fields)
        some_remotecontrol_key = len(
            list(set(all_vals) & set(self._remotecontrol_partner_fields))) > 0
        if (self.__class__._in_create_or_synchro or len(self) != 1 or
           not self.is_wua_partner or not some_remotecontrol_key):
            return resp
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census')
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'automatic_census_synchronization')
        # If the partner is archived / activated, then
        # automatic_census_synchronization = True (allways).
        active_in_vals = 'active' in vals
        if (enable_remotecontrol and can_be_sent_partners_census and
           (automatic_census_synchronization or active_in_vals)):
            record_archived = False
            if (active_in_vals and not vals['active']):
                record_archived = True
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
                            data, record_archived)
                    prefix_message = _('Remote Control: Updating remote '
                                       'control for partner (existing)')
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
                    if record.is_wua_partner:
                        data = self.populate_data_for_delete_partner(record)
                        if data:
                            synchronized_remotecontrol, error_message = \
                                self.delete_partner(
                                    url_remotecontrol_rest,
                                    url_remotecontrol_rest_username,
                                    url_remotecontrol_rest_password,
                                    data)
                            prefix_message = _('Remote Control: Deleting '
                                               'remote control for partner ')
                            suffix_message = 'OK'
                            if not synchronized_remotecontrol:
                                if not error_message:
                                    error_message = \
                                        _('Update error in remote control')
                                suffix_message = error_message
                            _logger = logging.getLogger(
                                self.__class__.__name__)
                            _logger.info(prefix_message + ' ' +
                                         str(record.partner_code) + '... ' +
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
                       url_remotecontrol_rest_password,
                       data, record_archived=False):
        return False, ''

    # Hook
    def populate_data_for_delete_partner(self, partner):
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
            record_archived = not self.active
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
                            data, record_archived)
                    prefix_message = _('Remote Control: Synchronizing remote '
                                       'control for partner')
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
                    self.__class__._in_create_or_synchro = True
                    self.updated_in_remotecontrol = True
                    self.__class__._in_create_or_synchro = False

    def do_synchronization_partners(self, active_partners,
                                    show_message=False):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
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
                partners = self.env['res.partner'].with_context(
                    active_test=False).browse(active_partners)
                if partners:
                    list_of_data = []
                    for partner in partners:
                        data = self.populate_data_for_update_partner(partner)
                        list_of_data.append(data)
                    if list_of_data:
                        partners_ok, partners_not_ok = \
                            self.synchronize_partners(
                                url_remotecontrol_rest,
                                url_remotecontrol_rest_username,
                                url_remotecontrol_rest_password,
                                list_of_data)
                        if partners_ok or partners_not_ok:
                            _logger = logging.getLogger(
                                self.__class__.__name__)
                            prefix_message = _('Remote Control: Synchronizing '
                                               'remote control for partners')
                            suffix_message = 'OK'
                            self.__class__._in_create_or_synchro = True
                            if partners_ok:
                                partners_ok_str = ''
                                for partner_code in partners_ok:
                                    self.env['res.partner'].with_context(
                                        active_test=False).search(
                                            [('partner_code', '=',
                                              partner_code)]).\
                                        updated_in_remotecontrol = True
                                    partners_ok_str = partners_ok_str + \
                                        ', ' + str(partner_code)
                                partners_ok_str = partners_ok_str[2:]
                                _logger.info(prefix_message + ': ' +
                                             partners_ok_str + '... ' +
                                             suffix_message)
                            if partners_not_ok:
                                suffix_message = _('Update error in remote '
                                                   'control')
                                partners_not_ok_str = ''
                                for partner_code in partners_not_ok:
                                    self.env['res.partner'].with_context(
                                        active_test=False).search(
                                            [('partner_code', '=',
                                              partner_code)]).\
                                        updated_in_remotecontrol = False
                                    partners_not_ok_str = \
                                        partners_not_ok_str + ', ' + \
                                        str(partner_code)
                                partners_not_ok_str = partners_not_ok_str[2:]
                                _logger.info(prefix_message + ': ' +
                                             partners_not_ok_str + '... ' +
                                             suffix_message)
                            self.__class__._in_create_or_synchro = False
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))

    def do_synchronization_all_partners(self, show_message=False):
        partner_ids = self.env['res.partner'].with_context(
            active_test=False).search([('is_wua_partner', '=', True)]).ids
        if partner_ids:
            self.do_synchronization_partners(partner_ids, show_message)
        if not show_message:
            return True

    # Hook
    def synchronize_partner(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data, record_archived=False):
        return False, ''

    # Hook
    def synchronize_partners(self, url_remotecontrol_rest,
                             url_remotecontrol_rest_username,
                             url_remotecontrol_rest_password, list_of_data):
        return None, None

    @api.multi
    def do_unsynchronization_partner(self):
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
                data = self.populate_data_for_delete_partner(self)
                if data:
                    synchronized_remotecontrol, error_message = \
                        self.delete_partner(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    prefix_message = _('Remote Control: Unsynchronizing '
                                       'remote control for partner ')
                    suffix_message = 'OK'
                    if not synchronized_remotecontrol:
                        if not error_message:
                            error_message = \
                                _('Update error in remote control')
                        suffix_message = error_message
                    _logger = logging.getLogger(
                        self.__class__.__name__)
                    _logger.info(prefix_message + ' ' +
                                 str(self.partner_code) + '... ' +
                                 suffix_message)
                    if not synchronized_remotecontrol:
                        raise exceptions.UserError(_('ERROR ') + ':\n\n' +
                                                   suffix_message)
                    self.__class__._in_create_or_synchro = True
                    self.updated_in_remotecontrol = False
                    self.__class__._in_create_or_synchro = False


class ResPartnerWaterconnection(models.Model):
    _inherit = 'res.partner.waterconnection'

    last_data_time = fields.Datetime(
        string='Last Capture Date',)

    last_total_volume = fields.Float(
        string='Total (m³)',
        digits=(32, 4),)

    last_waterflow = fields.Float(
        string='Waterconnection Waterflow (l/s)',
        digits=(32, 4),)

    last_valve_open = fields.Boolean(
        string='Valve Open',)

    last_valve_scheduled = fields.Boolean(
        string='Valve Scheluded',)

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='res_partner_waterconnection')
            """)
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(self.env.cr,
                                      'res_partner_waterconnection')
            try:
                self.env.cr.execute("""
                    CREATE OR REPLACE VIEW res_partner_waterconnection AS (
                    SELECT row_number() OVER() AS id, a.* FROM (
                        SELECT wpp1.partner_id, wpi1.waterconnection_id,
                        ww1.last_data_time, ww1.last_total_volume,
                        ww1.last_waterflow, ww1.last_valve_open,
                        ww1.last_valve_scheduled
                        FROM
                        wua_parcel_irrigationpoint wpi1 INNER JOIN
                        wua_waterconnection ww1 ON ww1.id =
                        wpi1.waterconnection_id INNER JOIN
                        wua_parcel_partnerlink wpp1 ON wpp1.parcel_id =
                        wpi1.parcel_id WHERE wpi1.type='WC'
                        GROUP BY  wpp1.partner_id, wpi1.waterconnection_id,
                        ww1.last_data_time, ww1.last_waterflow,
                        ww1.last_valve_open, ww1.last_valve_scheduled,
                        ww1.last_total_volume
                    ) a )
                    """)
            except Exception:
                print "Couldn't create res.partner.waterconnection view"
