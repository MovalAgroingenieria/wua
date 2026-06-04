# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models

_logger = logging.getLogger(__name__)

# Map for the position (0-based) inside GPR_DIAS bitmask to the schedule
# selection value of the day of the week.
# GPR_DIAS was designed as a 14-day (2-week) bitmask but only one week is
# used: the first 7 characters are the days of the week starting on
# Monday (index 0 = Monday). Positions 7-13 are ignored.
GPR_DIAS_TO_DAY = {
    0: '00_monday',
    1: '01_tuesday',
    2: '02_wednesday',
    3: '03_thursday',
    4: '04_friday',
    5: '05_saturday',
    6: '06_sunday',
}


class WuaWaterconnectionIrrigationSchedule(models.Model):
    _inherit = 'wua.waterconnection.irrigation.schedule'

    # Aux: build the lookup {(dirum, diriru, position): waterconnection}
    # from the configured Regacom waterconnections.
    def _get_regacom_wc_lookup(self, list_of_wc=None):
        if list_of_wc:
            waterconnections = list_of_wc.filtered(
                lambda w: w.telecontrol_associated == 'regacom')
        else:
            waterconnections = self.env['wua.waterconnection'].search([
                ('telecontrol_associated', '=', 'regacom'),
                ('irrigationshed_id.regacom_enabled', '=', True),
                ('irrigationshed_id.regacom_dirum', '!=', False),
                ('irrigationshed_id.regacom_diriru', '!=', False),
                ('regacom_position', '!=', False),
            ])
        lookup = {}
        for wc in waterconnections:
            key = '%s|%s|%s' % (
                wc.irrigationshed_id.regacom_dirum,
                wc.irrigationshed_id.regacom_diriru,
                wc.regacom_position)
            lookup[key] = wc
        return lookup

    # Aux: get the float hour from a 'HH:MM:SS' string.
    def _get_float_hour_from_str_regacom(self, hour):
        resp = 0.0
        if hour:
            time_split = hour.split(':')
            hours = float(time_split[0])
            minutes = float(time_split[1]) / 60 if len(time_split) > 1 else 0
            resp = hours + minutes
        return resp

    # Aux: get the list of day selection values active in a GPR_DIAS
    # bitmask. Only the first 7 positions (one week, starting on Monday)
    # are taken into account.
    def _get_irrigation_days_from_gpr_dias(self, gpr_dias):
        days = []
        if gpr_dias:
            for index, char in enumerate(gpr_dias):
                if char == '1' and index in GPR_DIAS_TO_DAY:
                    days.append(GPR_DIAS_TO_DAY[index])
        return days

    # Aux: build the schedule values for a single group/program row and a
    # single day.
    def _build_schedule_vals_regacom(self, wc, item, day):
        start_hour = self._get_float_hour_from_str_regacom(
            item.get('GRP_HORA_INICIO'))
        end_hour = self._get_float_hour_from_str_regacom(
            item.get('GRP_HORA_FIN'))
        duration = end_hour - start_hour
        if start_hour > end_hour:
            duration += 24
        state = '01_active' if item.get('PROG_ACTIVO') else '00_inactive'
        # Use PROG_NUMERO as the shift number (turn number).
        shift_number = item.get('PROG_NUMERO') or 1
        resp = {
            'waterconnection_id': wc.id,
            'state': state,
            'shift_number': shift_number,
            'irrigation_start_day': day,
            'irrigation_start_hour': start_hour,
            'irrigation_end_hour': end_hour,
            'irrigation_duration': duration,
            'max_irrigation_volume': item.get('PROG_CANTIDAD') or 0.0,
        }
        return resp

    # Get the groups/programs data from the Regacom SQL database.
    def _get_regacom_groups_programs(self):
        groups_programs = []
        try:
            procedure = self.env.ref(
                'remotecontrol_regacom.'
                'remotecontrol_regacom_procedure_groups_programs')
        except Exception:
            return groups_programs
        try:
            bag = {}
            for step in procedure.step_ids.sorted(
                    key=lambda s: s.sequence):
                bag = step.action_id.execute(bag=bag)
            groups_programs = bag.get('groups_programs', [])
        except Exception:
            _logger.exception(
                'Regacom: error getting groups/programs from SQL database')
        return groups_programs

    # Hook implemented: append Regacom schedules to the others.
    def do_import_waterconnection_irrigation_schedule_all(self, list_of_wc):
        others_wc_info = list(
            super(WuaWaterconnectionIrrigationSchedule, self).
            do_import_waterconnection_irrigation_schedule_all(list_of_wc))
        import_schedule = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_irrigation_schedule_from_waterconnections_regacom')
        if not import_schedule:
            return others_wc_info
        wc_info, error_message = \
            self.import_waterconnection_irrigation_schedule_regacom(list_of_wc)
        if wc_info:
            others_wc_info[0] += wc_info
        if error_message:
            others_wc_info[1] += ' - ' + error_message + '\n\n'
        return others_wc_info

    def import_waterconnection_irrigation_schedule_regacom(self, list_of_wc):
        wc_irr_schedule_all_info = []
        error_message = ''
        try:
            lookup = self._get_regacom_wc_lookup(list_of_wc)
            if not lookup:
                return [wc_irr_schedule_all_info, error_message]
            groups_programs = self._get_regacom_groups_programs()
            if not groups_programs:
                error_message = 'No groups/programs found in Regacom database'
                return [wc_irr_schedule_all_info, error_message]
            for item in groups_programs:
                key = '%s|%s|%s' % (
                    item.get('PROG_nDirUM'),
                    item.get('PROG_nDirIRU'),
                    item.get('PROG_N_VALVULA'))
                wc = lookup.get(key)
                if not wc:
                    continue
                days = self._get_irrigation_days_from_gpr_dias(
                    item.get('GPR_DIAS'))
                for day in days:
                    wc_irr_schedule_all_info.append(
                        self._build_schedule_vals_regacom(wc, item, day))
        except Exception as e:
            error_message = u'Regacom error:\n\n' + str(e)
        return [wc_irr_schedule_all_info, error_message]
