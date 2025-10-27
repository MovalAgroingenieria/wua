# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, _


class WuaControlreading(models.Model):
    _inherit = 'wua.controlreading'

    presresconsumption_id = fields.Many2one(
        string='Presresconsumption',
        comodel_name='wua.presresconsumption',
        ondelete='cascade',
        index=True,
    )

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
        # Create controlreading and assign them to presresconsumption
        controlreading = self.create({
            'watermeter_id':
                presresconsumption.waterconnection_id.watermeter_id.id,
            'reading_time': fields.Datetime.to_string(time_for_reading),
            'volume': last_volume,
            'initialization_reading': False,
            'from_import': False,
            'presresconsumption_id': presresconsumption.id,
        })
        # Set the adjustment volume on controlpresconsumption
        controlreading.controlpresconsumption_id.adjustement_volume = (
            presresconsumption.watering_volume)
        presresconsumption.controlreading_id = controlreading
        return controlreading

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
                            # Ensure ordered by reading time because newer
                            # must be deleted first
                            for control_reading in controlreadings_to_delete:
                                control_reading.unlink()
                            self.create({
                                'watermeter_id': reading['watermeter_id'],
                                'reading_time': reading_time,
                                'volume': reading['volume'],
                                'initialization_reading': False,
                                'from_import': False,
                                'validated': True,
                            })
                            for pr in presresconsumption_ids:
                                # Recreate controlreading for each
                                # presresconsumption
                                self._create_controlreading_for_pr(pr)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Controlreadings') +
                             '... ' +
                             str(number_of_readings))
            remotecontrol = self.env.ref(
                'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
            remotecontrol.message_post(
                body="Controlreadings from remote control: %s\n"
                     "Negative controlreadings: %s" % (
                         number_of_readings, number_of_negative_readings))
        if controlperiod_ids:
            controlperiod_ids = list(set(controlperiod_ids))
        return number_of_negative_readings, controlperiod_ids
