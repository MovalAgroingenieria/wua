# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _, exceptions


class WuaPressuresensor(models.Model):
    _inherit = 'wua.pressuresensor'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    # Empty, inherit
    telecontrol_associated = fields.Selection(
        [],
        string='Type of telecontrol associated')

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_pressuresensor = \
            self.env['wua.irrigation.configuration'].\
            import_from_pressuresensor_any()
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if import_from_pressuresensor is None:
            import_from_pressuresensor = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol and import_from_pressuresensor

    @api.multi
    def do_import_pressuresensormeasurements_from_pressuresensor(self):
        self.ensure_one()
        prefix_message = _('Remote Control: Starting import pressure '
                           'measurement in pressuresensor')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' +
                     str(self.name))
        data_pressuresensormeasurements = self.\
            env['wua.pressuresensormeasurement'].\
            do_import_pressure_measurements(save_data=False)
        pressuresensormeasurements = data_pressuresensormeasurements[0]
        if pressuresensormeasurements:
            pressuresensormeasurements = [
                x for x in pressuresensormeasurements if
                x['pressuresensor_id'] in [self.id]]
            self.env['wua.pressuresensormeasurement'].\
                save_pressure_measurements(pressuresensormeasurements)

    def do_import_pressuresensormeasurements_from_pressuresensors(
            self, active_pressuresensors):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        pressuresensors = self.env['wua.pressuresensor'].browse(
            active_pressuresensors)
        if pressuresensors:
            prefix_message = _('Remote Control: Starting reading in '
                               'pressure sensors')
            suffix_message = ''
            for pressuresensor in pressuresensors:
                suffix_message = suffix_message + ', ' + pressuresensor.name
            suffix_message = suffix_message[2:]
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' + suffix_message)
            data_pressuresensormeasurements = \
                self.env['wua.pressuresensormeasurement'].\
                do_import_pressure_measurements(save_data=False)
            pressuresensormeasurements = data_pressuresensormeasurements[0]
            if pressuresensormeasurements:
                pressuresensormeasurements = [
                    x for x in pressuresensormeasurements
                    if x['pressuresensor_id'] in active_pressuresensors]
                self.env['wua.pressuresensormeasurement'].\
                    save_pressuresensormeasurements(pressuresensormeasurements)
