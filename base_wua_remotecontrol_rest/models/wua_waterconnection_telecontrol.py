# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import api, models, fields, _, exceptions

_logger = logging.getLogger(__name__)

# Number of waterconnections processed per independent DB transaction.
# Smaller batches release row locks on wua_waterconnection faster.
_TELECONTROL_BATCH_SIZE = 20


class WuaWaterconnectionTelecontrol(models.Model):
    _name = 'wua.waterconnection.telecontrol'
    _description = 'Entity (waterconnection telecontrol)'
    _order = 'data_time, name'

    MAX_SIZE_NAME = 52
    MAX_COUNT_HIST = 24

    # Variable to extend
    PRETTY_ERROR_WATERMETER_DICT = {}
    # Variable to extend
    PRETTY_ERROR_VALVE_DICT = {}

    data_time = fields.Datetime(
        string='Capture Date',
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='cascade')

    total_volume = fields.Float(
        string='Total (m³)',
        digits=(32, 4))

    waterflow = fields.Float(
        string='Waterconnection Waterflow (l/s)',
        digits=(32, 4))

    valve_open = fields.Boolean(
        string='Valve Open',
    )

    valve_scheduled = fields.Boolean(
        string='Valve Scheluded',
    )

    valve_error = fields.Boolean(
        string='Valve With Error',
        default=False)

    valve_error_msg = fields.Char(
        string='Valve Error',
        size=254,
        default='')

    watermeter_error = fields.Boolean(
        string='Watermeter With Error',
        default=False)

    watermeter_error_msg = fields.Char(
        string='Watermeter Error',
        size=254,
        default='')

    name = fields.Char(
        string='Telecontrol Data',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    @api.depends('data_time', 'waterconnection_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.data_time:
                value = record.waterconnection_id.name + ' - ' + \
                    record.data_time
            record.name = value

    @api.model
    def create(self, vals):
        telecontrol_info = super(WuaWaterconnectionTelecontrol, self).\
            create(vals)
        telecontrol_info.waterconnection_id.write({
            'last_data_time': telecontrol_info.data_time,
            'last_total_volume': telecontrol_info.total_volume,
            'last_waterflow': telecontrol_info.waterflow,
            'last_valve_open': telecontrol_info.valve_open,
            'last_valve_scheduled': telecontrol_info.valve_scheduled,
            'last_valve_error': telecontrol_info.valve_error,
            'last_valve_error_msg': telecontrol_info.valve_error_msg,
            'last_watermeter_error': telecontrol_info.watermeter_error,
            'last_watermeter_error_msg': telecontrol_info.watermeter_error_msg,
        })
        return telecontrol_info

    # ------------------------------------------------------------------
    # Concurrency guard and batched save
    # ------------------------------------------------------------------
    def _acquire_cron_lock(self):
        """Try to acquire an advisory lock to prevent overlapping runs.
        Returns True if the lock was acquired, False otherwise."""
        lock_id = hash(
            'do_import_waterconnection_telecontrol_info') % (2 ** 31)
        self.env.cr.execute(
            "SELECT pg_try_advisory_xact_lock(%s)", (lock_id,))
        acquired = self.env.cr.fetchone()[0]
        if not acquired:
            _logger.warning(
                'Cron telecontrol info import: another instance is '
                'already running. Skipping this execution.')
        return acquired

    def _save_telecontrol_info_in_batches(self, wc_info):
        """Save telecontrol info in small independent DB transactions.

        Each batch commits independently, keeping row locks on
        ``wua_waterconnection`` short-lived and avoiding deadlocks
        with other crons that also write to the same rows.
        """
        # Deduplicate: keep only newest entry per waterconnection
        by_wc = {}
        for info in wc_info:
            wc_id = info['waterconnection_id']
            if (wc_id not in by_wc or
                    info['data_time'] > by_wc[wc_id]['data_time']):
                by_wc[wc_id] = info
        wc_info_deduped = list(by_wc.values())
        total = len(wc_info_deduped)
        saved = 0
        errors = 0
        for batch_start in range(0, total, _TELECONTROL_BATCH_SIZE):
            batch = wc_info_deduped[
                batch_start:batch_start + _TELECONTROL_BATCH_SIZE]
            batch_num = batch_start // _TELECONTROL_BATCH_SIZE + 1
            try:
                with self.env.registry.cursor() as new_cr:
                    new_env = api.Environment(
                        new_cr, self.env.uid, self.env.context)
                    new_env['wua.waterconnection.telecontrol']\
                        .save_waterconnection_telecontrol_info(
                            batch, update_log=False)
                    new_cr.commit()
                saved += len(batch)
            except Exception as e:
                _logger.error(
                    'Cron telecontrol info import: '
                    'batch %d failed: %s', batch_num, e)
                errors += len(batch)
        _logger.info(
            'Cron telecontrol info import: %d saved, %d errors',
            saved, errors)
        return saved, errors

    # Hook that will be implemented on all telecontrols, appending info
    def do_import_waterconnection_telecontrol_info_all(self):
        wc_info = []
        error_message = ''
        return [wc_info, error_message]

    @api.model
    def do_import_waterconnection_telecontrol_info(
            self, save_data=True, show_message=True):
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if not enable_remotecontrol:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
            return resp
        # Concurrency guard: skip if another instance is running.
        if not self._acquire_cron_lock():
            return resp
        # Phase 1 — Collect from remote control (HTTP, no DB writes).
        wc_info, error_message = \
            self.do_import_waterconnection_telecontrol_info_all()
        # Phase 2 — Refine (filter / transform).
        wc_info = self.refine_waterconnection_telecontrol_info(wc_info)
        # Phase 3 — Save in batches with independent transactions.
        if save_data and wc_info:
            self._save_telecontrol_info_in_batches(wc_info)
        # Phase 4 — Error notification (if API reported errors).
        if error_message:
            prefix_message = _('Remote Control: Error getting '
                               'waterconnection info')
            company_name = self.env.user.company_id.name
            website_url = self.env['ir.config_parameter'].get_param(
                "web.base.url")
            domain = self.env['ir.config_parameter'].get_param(
                "mail.catchall.domain")
            _logger.info(prefix_message + '... ' + error_message[:200])
            telecontrol_failed_template_id = self.env.ref(
                'base_wua_remotecontrol_rest.'
                'telecontrol_failed_email_template').id
            mail_template = self.env['mail.template'].browse(
                telecontrol_failed_template_id)
            mail_template.subject = '''
                Waterconnection remote control in %s
                has experienced some problem
            ''' % (domain or self.pool.db_name)
            mail_template.body_html = '''
                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                    <b><a href="%s">%s</a></p></b>
                    <br/>
                    <span>%s</span>
                </p>
            ''' % (website_url, company_name, error_message.replace(
                   '\n', '<br/>'))
            mail_template.send_mail(self.id, force_send=True)
        return resp

    def populate_data_for_import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        return None

    # Hook
    def import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        return None, ''

    def refine_waterconnection_telecontrol_info(self, wc_info):
        resp = []
        waterconnections = self.env['wua.waterconnection']
        for info in wc_info:
            filtered_waterconnection = waterconnections.search(
                [('name', '=', info['waterconnection'])])
            if filtered_waterconnection:
                waterconnection = filtered_waterconnection[0]
                conversion_factor = waterconnection.conversion_factor
                valve_error_msg = info['valve_error_msg']
                if valve_error_msg in self.PRETTY_ERROR_VALVE_DICT:
                    valve_error_msg = self.PRETTY_ERROR_VALVE_DICT[
                        valve_error_msg]
                watermeter_error_msg = info['watermeter_error_msg']
                if watermeter_error_msg in self.PRETTY_ERROR_WATERMETER_DICT:
                    watermeter_error_msg = self.PRETTY_ERROR_WATERMETER_DICT[
                        watermeter_error_msg]
                refined_wc_info = {
                    'waterconnection_id': waterconnection.id,
                    'valve_open': info['valve_open'],
                    'valve_scheduled': info['valve_scheduled'],
                    'valve_error': info['valve_error'],
                    'valve_error_msg': valve_error_msg,
                    'watermeter_error': info['watermeter_error'],
                    'watermeter_error_msg': watermeter_error_msg,
                    'total_volume': info['total_volume'],
                    'waterflow': info['waterflow'] / conversion_factor,
                    'data_time': info['data_time'],
                    }
                resp.append(refined_wc_info)
        return resp

    # -- Hooks for vendor-specific extra columns --------
    def _get_telecontrol_extra_columns(self):
        """Hook: extra column names for telecontrol INSERT.
        Override to add vendor-specific columns.
        """
        return []

    def _get_telecontrol_extra_values(self, info):
        """Hook: extra values for telecontrol INSERT.
        Must match _get_telecontrol_extra_columns.
        """
        return []

    def _get_wc_extra_update_columns(self):
        """Hook: extra column names for waterconnection
        UPDATE. E.g. ['last_valve_state'].
        """
        return []

    def _get_wc_extra_update_values(self, info):
        """Hook: extra values for waterconnection UPDATE.
        Must match _get_wc_extra_update_columns.
        """
        return []

    def _to_datetime(self, value):
        date_value = None
        if isinstance(value, datetime.datetime):
            date_value = value
        elif isinstance(value, basestring):
            date_value = fields.Datetime.from_string(value)
        return date_value

    def save_waterconnection_telecontrol_info(self, wc_info,
                                              update_log=True):
        if not wc_info:
            return
        cr = self.env.cr
        number_of_wc_info = len(wc_info)
        # Deduplicate: keep only newest per waterconnection
        by_wc = {}
        for info in wc_info:
            wc_id = info['waterconnection_id']
            if (wc_id not in by_wc or
                    info['data_time'] >
                    by_wc[wc_id]['data_time']):
                by_wc[wc_id] = info
        wc_info = list(by_wc.values())
        wc_ids = list(by_wc.keys())
        # 1. Current stats per waterconnection (one query)
        cr.execute(
            "SELECT waterconnection_id,"
            " MAX(data_time), COUNT(*)"
            " FROM wua_waterconnection_telecontrol"
            " WHERE waterconnection_id IN %s"
            " GROUP BY waterconnection_id",
            (tuple(wc_ids),))
        wc_stats = {}
        for wc_id, max_dt, cnt in cr.fetchall():
            wc_stats[wc_id] = (max_dt, cnt)
        # 2. Split data: insert newer, update-only equal timestamp
        to_insert = []
        to_update = []
        for info in wc_info:
            wc_id = info['waterconnection_id']
            stats = wc_stats.get(wc_id)
            if not stats:
                to_insert.append(info)
                to_update.append(info)
            else:
                info_dt = self._to_datetime(info['data_time'])
                max_dt = self._to_datetime(stats[0])
                if (info_dt and max_dt and info_dt > max_dt):
                    to_insert.append(info)
                    to_update.append(info)
                elif (info_dt and max_dt and info_dt == max_dt):
                    to_update.append(info)
        if not to_update:
            if update_log:
                _logger = logging.getLogger(
                    self.__class__.__name__)
                _logger.info(
                    'Remote Control: '
                    'No new telecontrol data.')
            return
        # 3. Waterconnection names for computed 'name'
        save_wc_ids = list(set(
            i['waterconnection_id'] for i in to_update))
        cr.execute(
            "SELECT id, name"
            " FROM wua_waterconnection"
            " WHERE id IN %s",
            (tuple(save_wc_ids),))
        wc_names = dict(cr.fetchall())
        # 4. Delete oldest beyond MAX_COUNT_HIST (SQL)
        for info in to_insert:
            wc_id = info['waterconnection_id']
            stats = wc_stats.get(wc_id)
            if (stats and
                    stats[1] >= self.MAX_COUNT_HIST):
                excess = (
                    stats[1] - self.MAX_COUNT_HIST + 1)
                cr.execute(
                    "DELETE FROM"
                    " wua_waterconnection_telecontrol"
                    " WHERE id IN ("
                    "  SELECT id FROM"
                    "  wua_waterconnection_telecontrol"
                    "  WHERE waterconnection_id = %s"
                    "  ORDER BY data_time ASC"
                    "  LIMIT %s)",
                    (wc_id, excess))
        # 5. Build INSERT query (with vendor hooks)
        now_utc = fields.Datetime.now()
        extra_cols = \
            self._get_telecontrol_extra_columns()
        extra_cols_sql = ''
        extra_phs_sql = ''
        if extra_cols:
            extra_cols_sql = (
                ', ' + ', '.join(extra_cols))
            extra_phs_sql = (
                ', ' + ', '.join(
                    ['%s'] * len(extra_cols)))
        insert_q = (
            "INSERT INTO"
            " wua_waterconnection_telecontrol"
            " (data_time, waterconnection_id,"
            " total_volume, waterflow,"
            " valve_open, valve_scheduled,"
            " valve_error, valve_error_msg,"
            " watermeter_error,"
            " watermeter_error_msg,"
            " name, create_uid, create_date,"
            " write_uid, write_date"
            "{xc})"
            " VALUES"
            " (%s, %s, %s, %s, %s, %s, %s, %s,"
            " %s, %s, %s, %s, %s, %s, %s"
            "{xp})"
        ).format(
            xc=extra_cols_sql,
            xp=extra_phs_sql)
        # 6. Build UPDATE query (with vendor hooks)
        extra_upd = \
            self._get_wc_extra_update_columns()
        extra_set_sql = ''
        if extra_upd:
            extra_set_sql = ', ' + ', '.join(
                c + ' = %s' for c in extra_upd)
        update_q = (
            "UPDATE wua_waterconnection SET"
            " last_data_time = %s,"
            " last_total_volume = %s,"
            " last_waterflow = %s,"
            " last_valve_open = %s,"
            " last_valve_scheduled = %s,"
            " last_valve_error = %s,"
            " last_valve_error_msg = %s,"
            " last_watermeter_error = %s,"
            " last_watermeter_error_msg = %s,"
            " write_uid = %s,"
            " write_date = %s"
            "{xs}"
            " WHERE id = %s"
        ).format(xs=extra_set_sql)
        # 7. Execute per record
        for info in to_insert:
            wc_id = info['waterconnection_id']
            wc_name = wc_names.get(wc_id, '')
            tc_name = ''
            if wc_name and info.get('data_time'):
                tc_name = (
                    wc_name + ' - ' +
                    info['data_time']
                )[:self.MAX_SIZE_NAME]

            insert_vals = (
                info['data_time'], wc_id,
                info['total_volume'],
                info['waterflow'],
                info['valve_open'],
                info['valve_scheduled'],
                info['valve_error'],
                info['valve_error_msg'],
                info['watermeter_error'],
                info['watermeter_error_msg'],
                tc_name,
                self.env.uid, now_utc,
                self.env.uid, now_utc,
            ) + tuple(
                self._get_telecontrol_extra_values(
                    info))
            cr.execute(insert_q, insert_vals)
        for info in to_update:
            wc_id = info['waterconnection_id']
            update_vals = (
                info['data_time'],
                info['total_volume'],
                info['waterflow'],
                info['valve_open'],
                info['valve_scheduled'],
                info['valve_error'],
                info['valve_error_msg'],
                info['watermeter_error'],
                info['watermeter_error_msg'],
                self.env.uid, now_utc,
            ) + tuple(
                self._get_wc_extra_update_values(
                    info)) + (wc_id,)
            cr.execute(update_q, update_vals)
        # 8. Invalidate ORM cache
        self.invalidate_cache()
        saved_count = len(to_insert)
        updated_count = len(to_update)
        if update_log:
            _logger = logging.getLogger(
                self.__class__.__name__)
            _logger.info(
                'Remote Control: Saved '
                'Waterconnection Telecontrol '
                'Info... %s inserted, %s updated/%s',
                saved_count, updated_count,
                number_of_wc_info)
