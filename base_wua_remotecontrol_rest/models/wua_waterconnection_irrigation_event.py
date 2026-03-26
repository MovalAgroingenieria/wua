# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import logging
from collections import defaultdict
from odoo import models, api, _, exceptions, fields, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Max events to create in a single transaction batch
BATCH_SIZE = 50


class WuaWaterconnectionIrrigationEvent(models.Model):
    _inherit = 'wua.waterconnection.irrigation.event'

    from_remotecontrol = fields.Boolean(
        string='From Remote Control',
        default=False,
        required=True,
    )

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        comodel_name='wua.waterpipe',
        compute='_compute_waterpipe_id',
        store=True,
        ondelete='set null',
    )

    @api.depends('irrigationshed_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if (record.irrigationshed_id and
                    record.irrigationshed_id.waterpipe_id):
                waterpipe_id = record.irrigationshed_id.waterpipe_id
            record.waterpipe_id = waterpipe_id

    # Hook that will be implemented on all telecontrols, appending info
    def do_import_waterconnection_irrigation_event_all(self, list_of_wc):
        wc_irr_event = []
        error_message = ''
        return [wc_irr_event, error_message]

    # ------------------------------------------------------------------
    # Concurrency guard: prevent overlapping cron executions
    # ------------------------------------------------------------------
    def _acquire_cron_lock(self):
        """Try to acquire an advisory lock to prevent overlapping runs.
        Returns True if the lock was acquired, False otherwise.
        Uses a fixed advisory lock ID derived from the cron purpose."""
        lock_id = hash('do_import_waterconnection_irrigation_event') % (
            2 ** 31)
        self.env.cr.execute(
            "SELECT pg_try_advisory_xact_lock(%s)", (lock_id,))
        acquired = self.env.cr.fetchone()[0]
        if not acquired:
            _logger.warning(
                'Cron irrigation event import: another instance is '
                'already running. Skipping this execution.')
        return acquired

    @api.model
    def do_import_waterconnection_irrigation_event(
            self, save_data=True, show_message=True, list_of_wc=False):
        """Main entry point called by the cron.
        - Acquire an advisory lock to prevent concurrent runs.
        - Collect data from the remote control API (HTTP, no heavy DB
          locks during this phase).
        - Refine events using a single prefetched query instead of N+1.
        - Save events in small batches using ``new_cursor`` so each
          batch is committed independently, keeping transactions short
          and releasing row-level locks on ``wua_waterconnection``
          quickly.
        """
        resp = [None, 0, '', None, 0]
        t_start = time.time()
        _logger.info('Cron irrigation event import: START')

        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            if show_message:
                raise exceptions.UserError(
                    _('The communication with the remote control '
                      'is not enabled.'))
            _logger.info(
                'Cron irrigation event import: remote control disabled')
            return resp
        # Concurrency guard
        if not self._acquire_cron_lock():
            return resp
        # Phase 1 — Collect data from remote control (HTTP calls)
        # This phase does NOT create/write DB records so it does not
        # hold row locks on wua_waterconnection.
        _logger.info('Cron irrigation event import: '
                     'Phase 1 - Collecting data from remote control...')
        t_collect = time.time()
        wc_irr_event, error_message = \
            self.do_import_waterconnection_irrigation_event_all(list_of_wc)
        _logger.info(
            'Cron irrigation event import: '
            'Phase 1 done - %d raw events collected in %.1fs',
            len(wc_irr_event), time.time() - t_collect)

        # Phase 2 — Refine (filter duplicates / already-imported)
        _logger.info('Cron irrigation event import: '
                     'Phase 2 - Refining events...')
        t_refine = time.time()
        wc_irr_event = self.refine_waterconnection_irrigation_event(
            wc_irr_event)
        _logger.info(
            'Cron irrigation event import: '
            'Phase 2 done - %d events after refine in %.1fs',
            len(wc_irr_event), time.time() - t_refine)

        # Phase 3 — Save in batches with independent transactions
        if save_data and wc_irr_event:
            _logger.info('Cron irrigation event import: '
                         'Phase 3 - Saving %d events in batches of %d...',
                         len(wc_irr_event), BATCH_SIZE)
            t_save = time.time()
            saved, errors = self._save_events_in_batches(wc_irr_event)
            _logger.info(
                'Cron irrigation event import: '
                'Phase 3 done - %d saved, %d errors in %.1fs',
                saved, errors, time.time() - t_save)

        # Phase 4 — Error notification (if any)
        if error_message:
            self._send_error_notification(error_message)

        elapsed = time.time() - t_start
        _logger.info(
            'Cron irrigation event import: END (total %.1fs)', elapsed)
        return resp

    def _send_error_notification(self, error_message):
        """Send email notification about import errors."""
        try:
            prefix_message = _('Remote Control: Error getting '
                               'waterconnection irrigation event')
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
            mail_template.subject = (
                'Waterconnection irrigation_event in %s '
                'has experienced some problem'
                % (domain or self.pool.db_name))
            mail_template.body_html = (
                '<p style="margin: 0px; padding: 0px; font-size: 13px;">'
                '<b><a href="%s">%s</a></b><br/>'
                '<span>%s</span></p>'
                % (website_url, company_name,
                   error_message.replace('\n', '<br/>')))
            mail_template.send_mail(self.id, force_send=True)
        except Exception:
            _logger.exception(
                'Cron irrigation event import: '
                'failed to send error notification email')

    def refine_waterconnection_irrigation_event(self, wc_irr_event):
        """Filter out events that are older than the last imported event
        for each waterconnection.

        Optimized: pre-fetch last events for all involved
        waterconnections in a single SQL query instead of N+1 ORM
        calls.
        """
        if not wc_irr_event:
            return []
        # Collect unique waterconnection IDs
        wc_ids = list(set(
            info['waterconnection_id'] for info in wc_irr_event))
        # Single SQL query: get the last irrigation_end_date and
        # irrigation_start_date per waterconnection.
        # This avoids:
        #   - N browse() calls
        #   - N accesses to last_irrigation_event_id (stored compute
        #     that loads all irrigation_event_ids)
        #   - Row locks on wua_waterconnection
        self.env.cr.execute("""
            SELECT waterconnection_id,
                   MAX(irrigation_end_date) AS last_end,
                   MAX(irrigation_start_date) AS last_start
            FROM wua_waterconnection_irrigation_event
            WHERE waterconnection_id IN %s
            GROUP BY waterconnection_id
        """, (tuple(wc_ids),))
        last_events = {}
        for row in self.env.cr.dictfetchall():
            last_events[row['waterconnection_id']] = {
                'end': row['last_end'],
                'start': row['last_start'],
            }
        resp = []
        for info in wc_irr_event:
            refined_wc_irr_event = {
                'waterconnection_id': info['waterconnection_id'],
                'irrigation_start_date': info['irrigation_start_date'],
                'irrigation_end_date': info['irrigation_end_date'],
                'irrigation_volume': info['irrigation_volume'],
            }
            if 'irrigation_area_static' in info:
                refined_wc_irr_event['irrigation_area_static'] = info[
                    'irrigation_area_static']
            last = last_events.get(info['waterconnection_id'])
            # Accept event if: no previous event exists, or
            # start_date >= last end_date and end_date > last start_date
            if (not last or (
                    last['end'] <= info['irrigation_start_date'] and
                    info['irrigation_end_date'] > last['start'])):
                resp.append(refined_wc_irr_event)
        _logger.info(
            'Cron irrigation event import: refine filtered %d -> %d events',
            len(wc_irr_event), len(resp))
        return resp

    def _save_events_in_batches(self, wc_irr_event):
        """Save irrigation events in small batches, each in its own
        DB transaction via ``new_cursor``.
        This ensures:
        - Row locks on ``wua_waterconnection`` (caused by stored
          compute fields ``last_irrigation_event_id`` and
          ``number_of_irrigation_events``) are held only for the
          duration of a small batch, not the entire cron run.
        - If one batch fails, previously committed batches are safe.
        - Other users can edit ``wua_waterconnection`` records between
          batches.
        Returns (saved_count, error_count).
        """
        total = len(wc_irr_event)
        saved_count = 0
        error_count = 0
        # Group events by waterconnection to minimise recomputation
        events_by_wc = defaultdict(list)
        for info in wc_irr_event:
            events_by_wc[info['waterconnection_id']].append(info)
        # Build flat list ordered by waterconnection (better for
        # grouped stored compute recomputation)
        ordered_events = []
        for wc_id in sorted(events_by_wc.keys()):
            ordered_events.extend(events_by_wc[wc_id])
        for batch_start in range(0, total, BATCH_SIZE):
            batch = ordered_events[batch_start:batch_start + BATCH_SIZE]
            batch_num = (batch_start // BATCH_SIZE) + 1
            t_batch = time.time()
            try:
                # Use a new cursor for an independent transaction
                with api.Environment.manage():
                    new_cr = self.pool.cursor()
                    try:
                        new_env = api.Environment(
                            new_cr, SUPERUSER_ID, self.env.context)
                        event_model = new_env[self._name]
                        for info in batch:
                            vals = {
                                'waterconnection_id':
                                    info['waterconnection_id'],
                                'irrigation_start_date':
                                    info['irrigation_start_date'],
                                'irrigation_end_date':
                                    info['irrigation_end_date'],
                                'irrigation_volume':
                                    info['irrigation_volume'],
                                'from_remotecontrol': True,
                            }
                            if 'irrigation_area_static' in info:
                                vals['irrigation_area_static'] = info[
                                    'irrigation_area_static']
                            event_model.create(vals)
                        new_cr.commit()
                        saved_count += len(batch)
                        _logger.info(
                            'Cron irrigation event import: '
                            'batch %d committed (%d events, %.1fs)',
                            batch_num, len(batch),
                            time.time() - t_batch)
                    except Exception:
                        new_cr.rollback()
                        error_count += len(batch)
                        _logger.exception(
                            'Cron irrigation event import: '
                            'batch %d FAILED (%d events)',
                            batch_num, len(batch))
                    finally:
                        new_cr.close()
            except Exception:
                error_count += len(batch)
                _logger.exception(
                    'Cron irrigation event import: '
                    'batch %d could not open cursor', batch_num)
        return saved_count, error_count

    def save_waterconnection_irrigation_event(self, wc_irr_event,
                                              update_log=True):
        """Legacy method kept for backward compatibility with manual
        calls (e.g. from waterconnection form buttons).

        For the cron, ``_save_events_in_batches`` is used instead.
        """
        number_of_wc_irr_event = len(wc_irr_event)
        if number_of_wc_irr_event > 0:
            for info in wc_irr_event:
                waterconnection_irrigation_event_params = {
                    'waterconnection_id': info['waterconnection_id'],
                    'irrigation_start_date': info['irrigation_start_date'],
                    'irrigation_end_date': info['irrigation_end_date'],
                    'irrigation_volume': info['irrigation_volume'],
                    'from_remotecontrol': True,
                }
                if ('irrigation_area_static' in info):
                    waterconnection_irrigation_event_params[
                        'irrigation_area_static'] = info[
                            'irrigation_area_static']
                self.create(waterconnection_irrigation_event_params)
            if update_log:
                _logger.info(
                    'Remote Control: Saved Irrigation events... %d',
                    number_of_wc_irr_event)
