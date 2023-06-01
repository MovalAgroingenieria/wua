# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


class WuaReservoir(models.Model):
    _inherit = 'wua.reservoir'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    # Empty, inherit
    telecontrol_associated = fields.Selection(
        [],
        string='Type of telecontrol associated')

    height_correction = fields.Float(
        string='Height correction for readings',
        digits=(32, 4),
        defaut=0.0,
        required=True,)

    _sql_constraints = [
        ('valid_height_correction',
         'CHECK (valid_height_correction >= 0)',
         'The height correction must be zero or positive.'),
        ]

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_reservoir = self.env['wua.irrigation.configuration'].\
            import_from_reservoir_any()
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if import_from_reservoir is None:
            import_from_reservoir = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_reservoir

    @api.multi
    def do_import_reservoirreadings_from_reservoir(self):
        self.ensure_one()
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        prefix_message = _('Remote Control: Starting reading in '
                           'reservoir')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' + str(self.name))
        model_reservoirreading = self.env['wua.reservoirreading']
        data_reservoirreadings = \
            model_reservoirreading.do_import_reservoirreadings(
                save_data=False)
        reservoirreadings = data_reservoirreadings[0]
        if reservoirreadings:
            reservoirreadings = \
                [x for x in reservoirreadings if x['reservoir_id']
                    in [self.id]]
            model_reservoirreading.save_reservoirreadings(
                reservoirreadings)

    def do_import_reservoirreadings_from_reservoirs(self, active_reservoirs):
        reservoirs = self.env['wua.reservoir'].browse(active_reservoirs)
        for reservoir in (reservoirs or []):
            reservoir.do_import_reservoirreadings_from_reservoir()
