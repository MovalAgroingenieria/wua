# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPumpgroup(models.Model):
    _inherit = 'wua.pumpgroup'

    _current_impulsion_pressure_deviceid = ''

    impulsion_pressure_deviceid = fields.Char(
        string='Device Identifier for impulsion pressure',
        size=30
    )

    impulsion_pressure_measurementid = fields.Char(
        string='Measurement Identifier for impulsion pressure',
        size=30
    )

    suction_pressure_deviceid = fields.Char(
        string='Device Identifier for suction pressure',
        size=30
    )

    suction_pressure_measurementid = fields.Char(
        string='Measurement Identifier for suction pressure',
        size=30
    )

    instantaneous_flow_deviceid = fields.Char(
        string='Device Identifier for instantaneous flow',
        size=30
    )

    instantaneous_flow_measurementid = fields.Char(
        string='Measurement Identifier for instantaneous flow',
        size=30
    )

    consumed_power_deviceid = fields.Char(
        string='Device Identifier for consumed power',
        size=30
    )

    consumed_power_measurementid = fields.Char(
        string='Measurement Identifier for consumed power',
        size=30
    )

    default_suction_pressure = fields.Float(
        string='Default Suction Pressure (mwc)',
        digits=(32, 2),
        default=0,
        required=True)

    impulsion_pressure_devicedesc = fields.Char(
        string='Device Description for impulsion pressure',
        size=50,
        readonly=True)

    impulsion_pressure_measurementdesc = fields.Char(
        string='Measurement Description for impulsion pressure',
        size=50,
        readonly=True)

    suction_pressure_devicedesc = fields.Char(
        string='Device Description for suction pressure',
        size=50,
        readonly=True)

    suction_pressure_measurementdesc = fields.Char(
        string='Measurement Description for suction pressure',
        size=50,
        readonly=True)

    instantaneous_flow_devicedesc = fields.Char(
        string='Device Description for instantaneous flow',
        size=50,
        readonly=True)

    instantaneous_flow_measurementdesc = fields.Char(
        string='Measurement Description for instantaneous flow',
        size=50,
        readonly=True)

    consumed_power_devicedesc = fields.Char(
        string='Device Description for consumed power',
        size=50,
        readonly=True)

    consumed_power_measurementdesc = fields.Char(
        string='Measurement Description for consumed power',
        size=50,
        readonly=True)

    connected_to_api = fields.Boolean(
        string='Connected to API',
        default=False,
        store=True,
        compute='_compute_connected_to_api')

    energymonitoring_enabled = fields.Boolean(
        string='Energy Monitoring enabled',
        compute='_compute_energymonitoring_enabled')

    @api.depends('impulsion_pressure_deviceid',
                 'impulsion_pressure_measurementid',
                 'instantaneous_flow_deviceid',
                 'instantaneous_flow_measurementid',
                 'consumed_power_deviceid',
                 'consumed_power_measurementid')
    def _compute_connected_to_api(self):
        for record in self:
            connected_to_api = False
            if ((record.impulsion_pressure_deviceid or
               record.impulsion_pressure_measurementid) and
               (record.instantaneous_flow_deviceid or
               record.instantaneous_flow_measurementid) and
               (record.consumed_power_deviceid or
               record.consumed_power_measurementid)):
                connected_to_api = True
            record.connected_to_api = connected_to_api

    @api.multi
    def _compute_energymonitoring_enabled(self):
        enable_energymonitoring = self.env['ir.values'].sudo().get_default(
            'wua.infrastructure.configuration', 'enable_energymonitoring')
        if enable_energymonitoring is None:
            enable_energymonitoring = False
        for record in self:
            record.energymonitoring_enabled = \
                enable_energymonitoring

    @api.model
    def create(self, vals):
        vals = self._update_vals_with_desc_fields(vals)
        return super(WuaPumpgroup, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            vals = self._update_vals_with_desc_fields(vals, True)
        return super(WuaPumpgroup, self).write(vals)

    def _update_vals_with_desc_fields(self, vals, is_write=False):
        if (('impulsion_pressure_deviceid' in vals) or
           ('impulsion_pressure_measurementid' in vals) or
           ('suction_pressure_deviceid' in vals) or
           ('suction_pressure_measurementid' in vals) or
           ('instantaneous_flow_deviceid' in vals) or
           ('instantaneous_flow_measurementid' in vals) or
           ('consumed_power_deviceid' in vals) or
           ('consumed_power_measurementid' in vals)):
            impulsion_pressure_devicedesc = ''
            impulsion_pressure_measurementdesc = ''
            suction_pressure_devicedesc = ''
            suction_pressure_measurementdesc = ''
            instantaneous_flow_devicedesc = ''
            instantaneous_flow_measurementdesc = ''
            consumed_power_devicedesc = ''
            consumed_power_measurementdesc = ''
            impulsion_pressure_deviceid = ''
            impulsion_pressure_measurementid = ''
            suction_pressure_deviceid = ''
            suction_pressure_measurementid = ''
            instantaneous_flow_deviceid = ''
            instantaneous_flow_measurementid = ''
            consumed_power_deviceid = ''
            consumed_power_measurementid = ''
            if 'impulsion_pressure_deviceid' in vals:
                impulsion_pressure_deviceid = \
                    vals['impulsion_pressure_deviceid']
            if 'suction_pressure_deviceid' in vals:
                suction_pressure_deviceid = \
                    vals['suction_pressure_deviceid']
            if 'instantaneous_flow_deviceid' in vals:
                instantaneous_flow_deviceid = \
                    vals['instantaneous_flow_deviceid']
            if 'consumed_power_deviceid' in vals:
                consumed_power_deviceid = \
                    vals['consumed_power_deviceid']
            if 'impulsion_pressure_measurementid' in vals:
                impulsion_pressure_measurementid = \
                    vals['impulsion_pressure_measurementid']
                if impulsion_pressure_deviceid == '' and is_write:
                    impulsion_pressure_deviceid = \
                        self.impulsion_pressure_deviceid
            if 'suction_pressure_measurementid' in vals:
                suction_pressure_measurementid = \
                    vals['suction_pressure_measurementid']
                if suction_pressure_deviceid == '' and is_write:
                    suction_pressure_deviceid = \
                        self.suction_pressure_deviceid
            if 'instantaneous_flow_measurementid' in vals:
                instantaneous_flow_measurementid = \
                    vals['instantaneous_flow_measurementid']
                if instantaneous_flow_deviceid == '' and is_write:
                    instantaneous_flow_deviceid = \
                        self.instantaneous_flow_deviceid
            if 'consumed_power_measurementid' in vals:
                consumed_power_measurementid = \
                    vals['consumed_power_measurementid']
                if consumed_power_deviceid == '' and is_write:
                    consumed_power_deviceid = \
                        self.consumed_power_deviceid
            desc_of_measurements = self._get_desc_of_measurements(
                [impulsion_pressure_deviceid,
                 impulsion_pressure_measurementid,
                 suction_pressure_deviceid,
                 suction_pressure_measurementid,
                 instantaneous_flow_deviceid,
                 instantaneous_flow_measurementid,
                 consumed_power_deviceid,
                 consumed_power_measurementid])
            if (desc_of_measurements and len(desc_of_measurements) == 8):
                impulsion_pressure_devicedesc = desc_of_measurements[0]
                impulsion_pressure_measurementdesc = desc_of_measurements[1]
                suction_pressure_devicedesc = desc_of_measurements[2]
                suction_pressure_measurementdesc = desc_of_measurements[3]
                instantaneous_flow_devicedesc = desc_of_measurements[4]
                instantaneous_flow_measurementdesc = desc_of_measurements[5]
                consumed_power_devicedesc = desc_of_measurements[6]
                consumed_power_measurementdesc = desc_of_measurements[7]
            if 'impulsion_pressure_deviceid' in vals:
                vals['impulsion_pressure_devicedesc'] = \
                    impulsion_pressure_devicedesc
            if 'suction_pressure_deviceid' in vals:
                vals['suction_pressure_devicedesc'] = \
                    suction_pressure_devicedesc
            if 'instantaneous_flow_deviceid' in vals:
                vals['instantaneous_flow_devicedesc'] = \
                    instantaneous_flow_devicedesc
            if 'consumed_power_deviceid' in vals:
                vals['consumed_power_devicedesc'] = \
                    consumed_power_devicedesc
            if 'impulsion_pressure_measurementid' in vals:
                vals['impulsion_pressure_measurementdesc'] = \
                    impulsion_pressure_measurementdesc
            if 'suction_pressure_measurementid' in vals:
                vals['suction_pressure_measurementdesc'] = \
                    suction_pressure_measurementdesc
            if 'instantaneous_flow_measurementid' in vals:
                vals['instantaneous_flow_measurementdesc'] = \
                    instantaneous_flow_measurementdesc
            if 'consumed_power_measurementid' in vals:
                vals['consumed_power_measurementdesc'] = \
                    consumed_power_measurementdesc
        return vals

    # Hook
    def _get_desc_of_measurements(self):
        return []

    @api.multi
    def do_get_measurements_of_pumpgroup(self):
        self.ensure_one()
        pumpgroup = self
        if (pumpgroup.energymonitoring_enabled and
           pumpgroup.connected_to_api):
            number_of_measurements = \
                self.env['wua.pumpgroupmeasurement'].do_import_measurements(
                    pumpgroup.pumpgroup_code)
        message_01_ok = _('Successful operation')
        message_01_error = _('UNSUCCESSFUL operation')
        message_02_ok = _('Number of measurements')
        message_02_error = _('Error in')
        message = ''
        buttons = [{'type': 'ir.actions.act_window_close',
                    'name': _('Close')}]
        if number_of_measurements >= 0:
            message = '<strong>' + message_01_ok + '</strong><br><br>' + \
                message_02_ok + ': ' + \
                '<strong>' + str(number_of_measurements) + '</strong>'
            if number_of_measurements > 0:
                buttons.append({
                    'type': 'ir.actions.act_window',
                    'name': _('Measurements'),
                    'res_model': 'wua.pumpgroupmeasurement',
                    'view_mode': 'form',
                    'views': [[False, 'list'], [False, 'form']],
                    'domain': [('id', 'in',
                                pumpgroup.pumpgroupmeasurement_ids.ids)],
                    'context': {'default_pumpgroup_id': self.id,
                                'search_default_of_active_agriculturalseason':
                                True},
                    'classes': 'btn-primary'})
        else:
            message = '<strong style="color:red;">' + \
                message_01_error + '</strong><br><br>' + \
                message_02_error + '...  ' + \
                str(pumpgroup.pumpgroup_code) + \
                ' (' + pumpgroup.name + ')'
        act_window = {
            'type': 'ir.actions.act_window.message',
            'title': _('Get measurements'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': buttons}
        return act_window
