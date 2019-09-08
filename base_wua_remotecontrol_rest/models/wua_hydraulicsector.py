# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_hydraulicsector = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_hydraulicsector')
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_hydraulicsector

    @api.multi
    def do_import_readings_from_hydraulicsector(self):
        self.ensure_one()
        prefix_message = _('Remote Control: Starting reading in '
                           'hydraulic sectors')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' +
                     str(self.name))
        data_readings = self.env['wua.reading'].do_import_readings(
            save_data=False)
        readings = data_readings[0]
        if readings:
            readings = [x for x in readings if x['hydraulicsector_id']
                        in [self.id]]
            self.env['wua.reading'].save_readings(readings)

    def do_import_readings_from_hydraulicsectors(self,
                                                 active_hydraulicsectors):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        hydraulicsectors = self.env['wua.hydraulicsector'].browse(
            active_hydraulicsectors)
        if hydraulicsectors:
            prefix_message = _('Remote Control: Starting reading in '
                               'hydraulic sectors')
            suffix_message = ''
            for hydraulicsector in hydraulicsectors:
                suffix_message = suffix_message + ', ' + hydraulicsector.name
            suffix_message = suffix_message[2:]
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' + suffix_message)
            data_readings = self.env['wua.reading'].do_import_readings(
                save_data=False)
            readings = data_readings[0]
            if readings:
                readings = [x for x in readings if x['hydraulicsector_id']
                            in active_hydraulicsectors]
                self.env['wua.reading'].save_readings(readings)
