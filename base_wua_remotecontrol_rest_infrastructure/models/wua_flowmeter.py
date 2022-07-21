# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_flowmeter = self.env['wua.irrigation.configuration'].\
            import_from_flowmeter_any()
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if import_from_flowmeter is None:
            import_from_flowmeter = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_flowmeter

    @api.multi
    def do_import_flowreadings_from_flowmeter(self):
        self.ensure_one()
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        if self.intake_id or self.waterpipe_id:
            prefix_message = _('Remote Control: Starting reading in '
                               'flowmeter')
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' +
                         str(self.name))
            model_flowreading = self.env['wua.flowreading']
            model_wpflowreading = self.env['wua.waterpipeflowreading']
            if self.intake_id:
                data_flowreadings = \
                    model_flowreading.do_import_flowreadings(
                        save_data=False)
                flowreadings = data_flowreadings[0]
                if flowreadings:
                    flowreadings = \
                        [x for x in flowreadings if x['flowmeter_id']
                         in [self.id]]
                    model_flowreading.save_flowreadings(flowreadings)
            else:
                data_waterpipeflowreadings = \
                    model_wpflowreading.do_import_waterpipeflowreadings(
                        save_data=False)
                waterpipeflowreadings = data_waterpipeflowreadings[0]
                if waterpipeflowreadings:
                    waterpipeflowreadings = \
                        [x for x in waterpipeflowreadings if x['flowmeter_id']
                         in [self.id]]
                    model_wpflowreading.save_waterpipeflowreadings(
                        waterpipeflowreadings)

    def do_import_flowreadings_from_flowmeters(self, active_flowmeters):
        flowmeters = self.env['wua.flowmeter'].browse(active_flowmeters)
        for flowmeter in (flowmeters or []):
            flowmeter.do_import_flowreadings_from_flowmeter()
