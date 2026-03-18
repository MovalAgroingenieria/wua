# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, _


class WuaControlreading(models.Model):
    _inherit = 'wua.controlreading'

    presresconsumption_id = fields.Many2one(
        string='Presresconsumption',
        comodel_name='wua.presresconsumption',
        ondelete='cascade',
        index=True,
    )

    @api.model
    def create(self, vals):
        # If there's an adjustement_volume in context, we need to pass it
        # to the controlpresconsumption that will be auto-created
        controlreading = super(WuaControlreading, self).create(vals)
        if (self.env.context.get('adjustement_volume') and
                controlreading.controlpresconsumption_id):
            adj_vol = self.env.context.get('adjustement_volume')
            cp = controlreading.controlpresconsumption_id
            # Use SQL to set adjustement_volume AND volume_real
            # together. We bypass ORM write to avoid triggering
            # the base write's sub/add_prorrated_value_to_subparcels
            # (which needs controlperiod data that may not exist) and
            # to avoid the provisional quota write's
            # regenerate_particularpresconsumptions (which would
            # recurse via _compute_hydraulic_infrastructure_data).
            self.env.cr.execute(
                "UPDATE wua_controlpresconsumption "
                "SET adjustement_volume = %s, "
                "    volume_real = COALESCE(volume, 0) + %s "
                "WHERE id = %s",
                (adj_vol, adj_vol, cp.id))
            cp.invalidate_cache(
                ['adjustement_volume', 'volume_real'])
            # Explicitly create particularpresconsumptions now that
            # volume_real is correct in the DB. The deferred compute
            # of _compute_hydraulic_infrastructure_data already ran
            # during super().create() but was a no-op (volume_real
            # was 0 at that point, so no ppcs were created).
            cp.create_particularpresconsumptions()
        # When creating a non-presresconsumption, non-initialization
        # reading, handle any existing presresconsumption readings
        # that need to be regenerated (posterior ones are deleted and
        # recreated; prior ones are archived). Skip when called from
        # save_controlreadings which handles this explicitly.
        if (not vals.get('presresconsumption_id') and
                not vals.get('initialization_reading') and
                not self.env.context.get('skip_pr_handling') and
                controlreading.watermeter_id.waterconnection_id):
            self._handle_presresconsumption_readings_on_create(
                controlreading)
        return controlreading

    def _create_controlreading_for_pr(
            self, presresconsumption):
        # Search last controlreading of this watermeter, get volume and set
        # the watering volume as adjustement_volume
        last_volume = 0.0
        time_for_reading = fields.Datetime.from_string(
            presresconsumption.request_time)
        # the request_time will be the start date, but we want the end date
        # so we get the watering duration in hours and add it to request_time
        if presresconsumption.watering_duration:
            time_for_reading = time_for_reading + datetime.timedelta(
                hours=presresconsumption.watering_duration)
        last_controlreading = self.search([
            ('watermeter_id', '=',
             presresconsumption.waterconnection_id.watermeter_id.id),
            ('reading_time', '<',
             fields.Datetime.to_string(time_for_reading))],
            order='reading_time desc', limit=1,
        )
        if last_controlreading:
            last_volume = last_controlreading.volume
        # Create controlreading with adjustement_volume in context
        # so it gets passed to the auto-created controlpresconsumption
        controlreading = self.with_context(
            adjustement_volume=presresconsumption.watering_volume,
        ).create({
            'watermeter_id':
                presresconsumption.waterconnection_id.watermeter_id.id,
            'reading_time': fields.Datetime.to_string(time_for_reading),
            'volume': last_volume,
            'initialization_reading': False,
            'from_import': False,
            'presresconsumption_id': presresconsumption.id,
        })
        presresconsumption.controlreading_id = controlreading
        return controlreading

    def _unlink_presresconsumption_controlreadings(
            self, controlreadings):
        """Delete presresconsumption-linked controlreadings bypassing
        the base unlink validations (is_last_reading and contiguous
        range checks), which can fail during programmatic batch
        cleanup when watermeter.last_controlreading_time doesn't
        match the expected sequence (e.g. when different watering
        durations cause reading times to be out of creation order).
        """
        if not controlreadings:
            return
        # Handle proration and hydric movements cleanup
        for cr in controlreadings:
            if cr.controlpresconsumption_id:
                if cr.validated:
                    cr.controlpresconsumption_id.\
                        sub_prorrated_value_to_subparcels()
                if (hasattr(cr.controlpresconsumption_id,
                            'controlhydricmovement_ids') and
                        cr.controlpresconsumption_id.
                        controlhydricmovement_ids):
                    cr.controlpresconsumption_id.\
                        controlhydricmovement_ids.with_context(
                            force_unlink=True).sudo().unlink()
        # Collect IDs before SQL operations
        cr_ids = controlreadings.ids
        cp_ids = [
            cp.id for cp in
            controlreadings.mapped('controlpresconsumption_id')
            if cp]
        # Clear FK from controlreading to controlpresconsumption
        # to avoid ON DELETE RESTRICT violation
        self.env.cr.execute(
            "UPDATE wua_controlreading "
            "SET controlpresconsumption_id = NULL "
            "WHERE id IN %s",
            (tuple(cr_ids),))
        # Delete controlpresconsumptions (this cascades to
        # particularpresconsumptions via their CASCADE FK)
        if cp_ids:
            self.env.cr.execute(
                "DELETE FROM wua_controlpresconsumption "
                "WHERE id IN %s",
                (tuple(cp_ids),))
        # Delete controlreadings
        self.env.cr.execute(
            "DELETE FROM wua_controlreading WHERE id IN %s",
            (tuple(cr_ids),))
        # Invalidate ORM cache
        self.env.invalidate_all()

    def _handle_presresconsumption_readings_on_create(
            self, controlreading):
        """When a real (non-presresconsumption) reading is created,
        handle existing presresconsumption readings for the same
        watermeter:
        - Archive prior ones (reading_time <= this reading) setting
          adjustement_volume to 0
        - Delete and recreate posterior ones (reading_time > this
          reading) so their previous volume reference is correct
        """
        watermeter_id = controlreading.watermeter_id.id
        reading_time = controlreading.reading_time
        # Archive prior presresconsumption readings
        prior_pr_readings = self.search([
            ('watermeter_id', '=', watermeter_id),
            ('presresconsumption_id', '!=', False),
            ('reading_time', '<=', reading_time),
            ('active', '=', True),
        ])
        if prior_pr_readings:
            prior_pr_readings.mapped(
                'controlpresconsumption_id').\
                write({'adjustement_volume': 0.0})
            self.archive_controlreadings(
                prior_pr_readings.mapped('id'))
        # Delete and recreate posterior presresconsumption readings
        posterior_pr_readings = self.search([
            ('watermeter_id', '=', watermeter_id),
            ('presresconsumption_id', '!=', False),
            ('reading_time', '>', reading_time),
        ], order='reading_time desc')
        if posterior_pr_readings:
            presresconsumptions = posterior_pr_readings.mapped(
                'presresconsumption_id')
            # Unset FK (ondelete='restrict')
            presresconsumptions.write({'controlreading_id': None})
            self._unlink_presresconsumption_controlreadings(
                posterior_pr_readings)
            # Recreate in natural order (oldest to newest)
            for pr in presresconsumptions.sorted(
                    key=lambda r: r.request_time):
                self._create_controlreading_for_pr(pr)
            self._update_watermeter_last_reading(
                controlreading.watermeter_id)

    # Inherit and overwrite method, now we will get the day of the reading_time
    # of the reading and check if there is any active controlreading related
    # to a presresconsumption with reading_time < = reading_time we will
    # archive it
    def save_controlreadings(self, readings, update_log=True):
        number_of_readings = len(readings)
        number_of_negative_readings = 0
        controlperiod_ids = []
        if number_of_readings > 0:
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
            controlperiod_model = self.env['wua.controlperiod']
            for reading in readings:
                previous_reading = self.env['wua.controlreading'].search_count(
                    [('watermeter_id', '=', reading['watermeter_id']),
                     ('presresconsumption_id', '=', False),
                     ('reading_time', '<=', reading_time),
                     ])
                if not previous_reading:
                    self.create({
                        'watermeter_id': reading['watermeter_id'],
                        'reading_time': reading_time,
                        'volume': reading['volume'],
                        'initialization_reading': True,
                        })
                else:
                    is_negative, negative_volume = \
                        self.is_negative_controlreading(reading)
                    if is_negative:
                        self.env['wua.negative.controlreading'].create({
                            'watermeter_id': reading['watermeter_id'],
                            'reading_time': reading_time,
                            'volume': reading['volume'],
                            'controlpresconsumption_volume': negative_volume,
                            })
                        number_of_negative_readings = \
                            number_of_negative_readings + 1
                    else:
                        ref_date = reading_time[0:10]
                        controlperiod = \
                            controlperiod_model._get_control_period(ref_date)
                        if controlperiod:
                            controlperiod_ids.append(controlperiod.id)
                        watermeter = self.env['wua.watermeter'].browse(
                            reading['watermeter_id'])
                        # Archive all presresconumptions that exists prior to
                        # this reading_time for this watermeter
                        if watermeter.waterconnection_id:
                            # search controlreadings that are active,
                            # with reading_time <= to reading_time  and with a
                            # presresconsumption_id and archive them
                            controlreadings_to_archive = \
                                self.env['wua.controlreading'].search([
                                    ('watermeter_id', '=',
                                     reading['watermeter_id']),
                                    ('presresconsumption_id', '!=', False),
                                    ('reading_time', '<=', reading_time),
                                    ('active', '=', True),
                                ])
                            if controlreadings_to_archive:
                                # set the controlpresconsumptions with
                                # adjustment volume to 0
                                controlreadings_to_archive.mapped(
                                    'controlpresconsumption_id').\
                                    write({'adjustement_volume': 0.0})
                                self.archive_controlreadings(
                                    controlreadings_to_archive.mapped('id'))
                            # Now we must search posible controlreadings with
                            # presresconsumption for this watermeter that
                            # have reading_time > to reading_time and delete
                            # them to recreate them after controlreading
                            # creation
                            controlreadings_to_delete = \
                                self.env['wua.controlreading'].search([
                                    ('watermeter_id', '=',
                                     reading['watermeter_id']),
                                    ('presresconsumption_id', '!=', False),
                                    ('reading_time', '>', reading_time),
                                ], order='reading_time desc')
                            presresconsumption_ids = \
                                controlreadings_to_delete.mapped(
                                    'presresconsumption_id')
                            # Unset, because ondelete='restrict'
                            presresconsumption_ids.write(
                                {'controlreading_id': None})
                            # Use helper to delete bypassing base
                            # unlink validations (is_last_reading,
                            # contiguous range) which can fail during
                            # batch programmatic cleanup
                            self.\
                                _unlink_presresconsumption_controlreadings(
                                    controlreadings_to_delete)
                            self.with_context(
                                skip_pr_handling=True,
                            ).create({
                                'watermeter_id': reading['watermeter_id'],
                                'reading_time': reading_time,
                                'volume': reading['volume'],
                                'initialization_reading': False,
                                'from_import': False,
                                'validated': True,
                            })
                            # Recreate in natural order (oldest to newest)
                            for pr in presresconsumption_ids.sorted(
                                    key=lambda r: r.request_time):
                                # Recreate controlreading for each
                                # presresconsumption
                                self._create_controlreading_for_pr(pr)
                            # Fix watermeter last reading (base create
                            # always sets it to the created reading's
                            # time, which may not be the newest when
                            # presresconsumption durations vary)
                            self._update_watermeter_last_reading(
                                watermeter)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Controlreadings') +
                             '... ' +
                             str(number_of_readings))
            remotecontrol = self.env.ref(
                'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
            remotecontrol.message_post(
                subject=_('Remote Control: Controlreadings Saved'),
                body="Controlreadings from remote control: %s<br/>"
                     "Negative controlreadings: %s" % (
                         number_of_readings, number_of_negative_readings),
                message_type='email',
                subtype='mail.mt_comment',
            )
        if controlperiod_ids:
            controlperiod_ids = list(set(controlperiod_ids))
        return number_of_negative_readings, controlperiod_ids
