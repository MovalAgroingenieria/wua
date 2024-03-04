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
        can_be_sent_partners_census = \
            self.env['wua.irrigation.configuration'].\
            can_be_sent_partners_census_any()
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if can_be_sent_partners_census is None:
            can_be_sent_partners_census = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & can_be_sent_partners_census

    def send_partner_on_creation(self, telecontrol, new_partner, vals):
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'can_be_sent_partners_census_' +
            telecontrol)
        automatic_census_synchronization = \
            self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'automatic_census_synchronization_' + telecontrol)
        if (can_be_sent_partners_census and automatic_census_synchronization):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'url_remotecontrol_rest_' +
                telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                    url_remotecontrol_rest_password):
                populate_function = getattr(
                    self, 'populate_data_for_send_new_partner_' + telecontrol)
                data = populate_function(vals)
                if data:
                    send_function = getattr(
                        self, 'send_new_partner_' + telecontrol)
                    synchronized_remotecontrol, error_message = \
                        send_function(
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

    # Hook to use on every telecontrol
    def send_partner_on_creation_telecontrol(self, new_partner, vals):
        pass

    @api.model
    def create(self, vals):
        self.__class__._in_create_or_synchro = True
        new_partner = super(ResPartner, self).create(vals)
        if 'is_wua_partner' in vals and vals['is_wua_partner']:
            enable_remotecontrol = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'enable_remotecontrol')
            if (enable_remotecontrol):
                self.send_partner_on_creation_telecontrol(new_partner, vals)
        self.__class__._in_create_or_synchro = False
        return new_partner

    def send_partner_on_write(self, telecontrol, vals):
        some_remotecontrol_key = False
        all_vals = vals.keys()
        # Intersect the vals written and the possible keys that will trigger
        # the update (_remotecontrol_partner_fields)
        remotecontrol_partner_fields = getattr(
            self, '_remotecontrol_partner_fields_' + telecontrol, [])
        some_remotecontrol_key = len(
            list(set(all_vals) & set(remotecontrol_partner_fields))) > 0
        if (not some_remotecontrol_key):
            return
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_' + telecontrol)
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'automatic_census_synchronization_' + telecontrol)
        # If the partner is archived / activated, then
        # automatic_census_synchronization = True (always).
        active_in_vals = 'active' in vals
        if (can_be_sent_partners_census and
                (automatic_census_synchronization or active_in_vals)):
            record_archived = False
            if (active_in_vals and not vals['active']):
                record_archived = True
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'url_remotecontrol_rest_' +
                telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
               url_remotecontrol_rest_password):
                populate_function = getattr(
                    self, 'populate_data_for_update_partner_' + telecontrol)
                data = populate_function(self)
                if data:
                    update_partner_function = getattr(
                        self, 'update_partner_' + telecontrol)
                    synchronized_remotecontrol, error_message = \
                        update_partner_function(
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

    # Hook to use on every telecontrol
    def send_partner_on_write_telecontrol(self, vals):
        pass

    @api.multi
    def write(self, vals):
        resp = super(ResPartner, self).write(vals)
        if (self.__class__._in_create_or_synchro or len(self) != 1 or
           not self.is_wua_partner):
            return resp
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            self.send_partner_on_write_telecontrol(vals)
        return resp

    def unlink_partner_on_unlink(self, telecontrol):
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_' + telecontrol)
        automatic_census_synchronization = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'automatic_census_synchronization_' + telecontrol)
        if (can_be_sent_partners_census and automatic_census_synchronization):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'url_remotecontrol_rest_' + telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                    url_remotecontrol_rest_password):
                for record in self:
                    if record.is_wua_partner:
                        # Get populate data from the telecontrol being
                        # processed
                        # Do this outside the loop?
                        populate_function = getattr(
                            self, 'populate_data_for_delete_partner_' +
                            telecontrol)
                        data = populate_function(record)
                        if data:
                            delete_function = getattr(
                                self, 'delete_partner_' +
                                telecontrol)
                            synchronized_remotecontrol, error_message = \
                                delete_function(
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

    # Hook to use on every telecontrol
    def unlink_partner_on_unlink_telecontrol(self):
        pass

    @api.multi
    def unlink(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            self.unlink_partner_on_unlink_telecontrol()
        return super(ResPartner, self).unlink()

    def create_partner_on_syncrhonize(self, telecontrol):
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_' + telecontrol)
        if (can_be_sent_partners_census):
            record_archived = not self.active
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'url_remotecontrol_rest_' + telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
               url_remotecontrol_rest_password):
                populate_function = getattr(
                    self, 'populate_data_for_update_partner_' + telecontrol)
                data = populate_function(self)
                if data:
                    sync_function = getattr(
                        self, 'synchronize_partner_' + telecontrol)
                    synchronized_remotecontrol, error_message = \
                        sync_function(
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

    # Hook to use on every telecontrol
    def create_partner_on_synchronize_telecontrol(self):
        pass

    @api.multi
    def do_synchronization_partner(self):
        self.ensure_one()
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            self.create_partner_on_synchronize_telecontrol()

    def create_partners_on_synchronize(self, active_partners, telecontrol):
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_' + telecontrol)
        if (can_be_sent_partners_census):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'url_remotecontrol_rest_' + telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
               url_remotecontrol_rest_password):
                partners = self.env['res.partner'].with_context(
                    active_test=False).browse(active_partners)
                if partners:
                    list_of_data = []
                    for partner in partners:
                        populate_function = getattr(
                            self, 'populate_data_for_update_partner_' +
                            telecontrol)
                        data = populate_function(partner)
                        list_of_data.append(data)
                    if list_of_data:
                        sync_function = getattr(
                            self, 'synchronize_partners_' + telecontrol)
                        partners_ok, partners_not_ok = \
                            sync_function(
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

    # Hook to use on every telecontrol
    def create_partners_on_synchronize_telecontrol(self, active_partners):
        pass

    def do_synchronization_partners(self, active_partners,
                                    show_message=False):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            self.create_partners_on_synchronize_telecontrol(active_partners)
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

    def unlink_partner_on_unsyncrhonize(self, telecontrol):
        can_be_sent_partners_census = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_' + telecontrol)
        if (can_be_sent_partners_census):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'url_remotecontrol_rest_' + telecontrol)
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_' + telecontrol)
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_' + telecontrol)
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                    url_remotecontrol_rest_password):
                populate_function = getattr(
                    self, 'populate_data_for_delete_partner_' + telecontrol)
                data = populate_function(self)
                if data:
                    delete_function = getattr(
                        self, 'delete_partner_' + telecontrol)
                    synchronized_remotecontrol, error_message = \
                        delete_function(
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

    # Hook to use on every telecontrol
    def unlink_partner_on_unsynchronize_telecontrol(self):
        pass

    @api.multi
    def do_unsynchronization_partner(self):
        self.ensure_one()
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            self.unlink_partner_on_unsynchronize_telecontrol()

    # If the user is a portal user, show the water connections if
    # it is the water payer.
    def get_res_partner_waterconnections_action(self):
        act_window = \
            super(ResPartner, self).get_res_partner_waterconnections_action()
        if (act_window and 'domain' in act_window and act_window['domain'] and
           self.env.user.has_group('base_wua.group_wua_portal_user')):
            id_of_partner = 0
            domain = act_window['domain']
            initial_condition = domain[0]
            if (initial_condition[0] == 'partner_id' and
               initial_condition[1] == '='):
                id_of_partner = initial_condition[2]
            if id_of_partner:
                waterconnection_ids = \
                    self.sudo().get_waterconnections_of_partner_as_water_payer(
                        id_of_partner)
                domain = [('waterconnection_id', 'in', waterconnection_ids)]
                act_window['domain'] = domain
        return act_window

    def get_waterconnections_of_partner_as_water_payer(self, id_of_partner):
        resp = []
        waterconnections_of_partner = \
            self.env['res.partner.waterconnection'].search(
                [('partner_id', '=', id_of_partner)])
        if waterconnections_of_partner:
            for wc_of_partner in waterconnections_of_partner:
                parcel_ids = []
                irrigationpoints = \
                    wc_of_partner.waterconnection_id.irrigationpoint_ids
                for irrigationpoint in (irrigationpoints or []):
                    parcel_ids.append(irrigationpoint.parcel_id.id)
                if parcel_ids:
                    partner_pays_water = False
                    for parcel_id in parcel_ids:
                        partnerlink = \
                            self.env['wua.parcel.partnerlink'].search(
                                [('partner_id', '=', id_of_partner),
                                 ('parcel_id', '=', parcel_id)])
                        if partnerlink:
                            partnerlink = partnerlink[0]
                            if partnerlink.water_costs_percentage > 0:
                                partner_pays_water = True
                                break
                    if partner_pays_water:
                        resp.append(wc_of_partner.waterconnection_id.id)
        return resp


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
            self.env.cr.savepoint()
            self.env.cr.execute("""
                CREATE OR REPLACE VIEW res_partner_waterconnection AS (
                SELECT row_number() OVER() AS id, a.* FROM (
                    SELECT wpp1.partner_id, wpi1.waterconnection_id, 
                    wpi1.active,
                    ww1.last_reading_time, ww1.last_reading_value,
                    wpc1.volume_real,
                    ww1.last_data_time, ww1.last_total_volume,
                    ww1.last_waterflow, ww1.last_valve_open,
                    ww1.last_valve_scheduled
                    FROM
                    wua_parcel_irrigationpoint wpi1 INNER JOIN
                    wua_waterconnection ww1 ON ww1.id =
                    wpi1.waterconnection_id INNER JOIN
                    wua_parcel_partnerlink wpp1 ON wpp1.parcel_id =
                    wpi1.parcel_id
                    LEFT JOIN wua_presconsumption wpc1
                    ON wpc1.waterconnection_id = ww1.id
                    AND wpc1.reading_end_time = ww1.last_reading_time
                    WHERE wpi1.type='WC' AND
                    ww1.watermeter_id IS NOT NULL
                    GROUP BY  wpp1.partner_id, wpi1.waterconnection_id, 
                    wpi1.active,
                    ww1.last_reading_time, ww1.last_reading_value,
                    wpc1.volume_real,
                    ww1.last_data_time, ww1.last_waterflow,
                    ww1.last_valve_open, ww1.last_valve_scheduled,
                    ww1.last_total_volume
                ) a )
                """)
        except Exception:
            self.env.cr.rollback()
