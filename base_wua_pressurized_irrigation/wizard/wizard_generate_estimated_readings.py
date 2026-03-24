# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import time

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

LAST_READING_SEARCH_BATCH = 250


class WizardGenerateEstimatedReadings(models.TransientModel):
    _name = 'wizard.generate.estimated.readings'
    _description = 'Wizard to Generate Estimated Readings'

    date = fields.Datetime(
        string='Reading Date',
        required=True,
        default=fields.Datetime.now,
    )

    def action_generate_readings(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return {'type': 'ir.actions.act_window_close'}
        t0 = time.time()
        waterconnections = self.env['wua.waterconnection'].browse(active_ids)
        without_meter = waterconnections.filtered(lambda c: not c.watermeter_id)
        if without_meter:
            raise UserError(
                _('The following Water connections need a Water meter: %s')
                % ', '.join(without_meter.mapped('display_name')))
        Reading = self.env['wua.reading']
        t1 = time.time()
        groups = Reading.read_group(
            [('waterconnection_id', 'in', active_ids)],
            ['reading_time:max', 'waterconnection_id'],
            ['waterconnection_id'],
        )
        _logger.info(
            'wizard generate_estimated_readings: read_group %s groups in %.2fs',
            len(groups), time.time() - t1)
        last_volume = {}
        if groups:
            t2 = time.time()
            for start in range(0, len(groups), LAST_READING_SEARCH_BATCH):
                batch = groups[start:start + LAST_READING_SEARCH_BATCH]
                domain = []
                n = len(batch)
                for i in range(n - 1):
                    domain.append('|')
                for g in batch:
                    domain.append('&')
                    domain.append(('waterconnection_id', '=', g['waterconnection_id'][0]))
                    domain.append(('reading_time', '=', g['reading_time']))
                last_recs = Reading.search(domain)
                for r in last_recs:
                    last_volume[r.waterconnection_id.id] = r.volume
            _logger.info(
                'wizard generate_estimated_readings: search last_recs %s rows in %d batches in %.2fs',
                len(last_volume), (len(groups) + LAST_READING_SEARCH_BATCH - 1) // LAST_READING_SEARCH_BATCH,
                time.time() - t2)
        t3 = time.time()
        conn_data = self.env['wua.waterconnection'].search_read(
            [('id', 'in', active_ids)],
            ['id', 'watermeter_id', 'estimated_monthly_consumption'],
        )
        _logger.info(
            'wizard generate_estimated_readings: search_read conn_data %s rows in %.2fs',
            len(conn_data), time.time() - t3)
        # Precompute previous-reading data per watermeter to avoid 2 search() per create()
        wc_to_wm = {}
        init_watermeter_ids = set()
        for row in conn_data:
            wm_id = row.get('watermeter_id')
            if not wm_id:
                continue
            if isinstance(wm_id, (list, tuple)):
                wm_id = wm_id[0]
            wc_to_wm[row['id']] = wm_id
            if row['id'] not in last_volume:
                init_watermeter_ids.add(wm_id)
        previous_by_wm = {}
        for g in (groups or []):
            wc_id = g['waterconnection_id'][0]
            if wc_id not in wc_to_wm:
                continue
            previous_by_wm[wc_to_wm[wc_id]] = {
                'reading_time': g['reading_time'],
                'volume': last_volume.get(wc_id, 0),
            }
        Reading = Reading.with_context(
            estimated_wizard_previous_reading=previous_by_wm,
            estimated_wizard_init_watermeter_ids=frozenset(init_watermeter_ids),
            estimated_wizard_skip_watermeter_write=True,
            estimated_wizard_defer_perunitareas=True,
        )
        reading_date = self.date
        created = 0
        t4 = time.time()
        log_every = 500
        for row in conn_data:
            wc_id = row['id']
            wm_id = row.get('watermeter_id')
            if not wm_id:
                continue
            if isinstance(wm_id, (list, tuple)):
                wm_id = wm_id[0]
            consumption = row.get('estimated_monthly_consumption') or 0
            prev = last_volume.get(wc_id, 0)
            Reading.create({
                'watermeter_id': wm_id,
                'reading_time': reading_date,
                'volume': prev + consumption,
                'reading_type': '01_estimated',
                'validated': False,
                'initialization_reading': wc_id not in last_volume,
            })
            created += 1
            if created % log_every == 0:
                _logger.info(
                    'wizard generate_estimated_readings: created %s readings in %.2fs so far',
                    created, time.time() - t4)
        # Batch update watermeters and per-unit areas (deferred from create())
        if created:
            wm_ids = []
            for row in conn_data:
                wm_id = row.get('watermeter_id')
                if not wm_id:
                    continue
                if isinstance(wm_id, (list, tuple)):
                    wm_id = wm_id[0]
                wm_ids.append(wm_id)
            if wm_ids:
                t5 = time.time()
                created_readings = Reading.search([
                    ('watermeter_id', 'in', wm_ids),
                    ('reading_time', '=', reading_date),
                ])
                # Prefetch for watermeter update
                created_readings.mapped('presconsumption_volume_real')
                # One update per watermeter (same meter may appear in several readings)
                done_wm = set()
                for reading in created_readings:
                    wm = reading.watermeter_id
                    if wm.id in done_wm:
                        continue
                    done_wm.add(wm.id)
                    wm.write({
                        'last_reading_time': reading.reading_time,
                        'last_reading_value': reading.volume,
                        'last_reading_consumption': reading.presconsumption_volume_real or 0,
                        'last_reading_type': reading.reading_type,
                    })
                presconsumptions = created_readings.mapped('presconsumption_id')
                for pres in presconsumptions:
                    pres.update_volume_perunitareas()
                _logger.info(
                    'wizard generate_estimated_readings: batch update watermeters + perunitareas in %.2fs',
                    time.time() - t5)
        create_elapsed = time.time() - t4
        _logger.info(
            'wizard generate_estimated_readings: created %s readings in %.2fs (%.3fs per record)',
            created, create_elapsed, create_elapsed / created if created else 0)
        total_elapsed = time.time() - t0
        _logger.info(
            'wizard generate_estimated_readings: total %.2fs for %s connections, %s readings',
            total_elapsed, len(active_ids), created)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Readings'),
            'res_model': 'wua.reading',
            'view_mode': 'tree,form',
            'domain': [('waterconnection_id', 'in', active_ids)],
        }
