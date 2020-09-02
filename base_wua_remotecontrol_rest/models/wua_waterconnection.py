# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    conversion_factor = fields.Integer(
        string="Conversion Factor",
        required=True,
        default=1)

    _sql_constraints = [
        ('conversion_factor_positive', 'CHECK (conversion_factor > 0)',
         'Conversion factor must be greater than 0.'),
        ]

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_waterconnection = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_waterconnection')
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_waterconnection

    @api.multi
    def do_import_readings_from_waterconnection(self):
        self.ensure_one()
        prefix_message = _('Remote Control: Starting reading in '
                           'water connections')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' +
                     str(self.name))
        data_readings = self.env['wua.reading'].do_import_readings(
            save_data=False)
        readings = data_readings[0]
        if readings:
            readings = [x for x in readings if x['waterconnection_id']
                        in [self.id]]
            self.env['wua.reading'].save_readings(readings)

    def do_import_readings_from_waterconnections(self,
                                                 active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        if waterconnections:
            prefix_message = _('Remote Control: Starting reading in '
                               'water connections')
            suffix_message = ''
            for waterconnection in waterconnections:
                suffix_message = suffix_message + ', ' + waterconnection.name
            suffix_message = suffix_message[2:]
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' + suffix_message)
            data_readings = self.env['wua.reading'].do_import_readings(
                save_data=False)
            readings = data_readings[0]
            if readings:
                readings = [x for x in readings if x['waterconnection_id']
                            in active_waterconnections]
                self.env['wua.reading'].save_readings(readings)
