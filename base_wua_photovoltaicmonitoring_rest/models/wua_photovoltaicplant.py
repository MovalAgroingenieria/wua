# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPhotovoltaicplant(models.Model):
    _inherit = 'wua.photovoltaicplant'

    generated_power_deviceid = fields.Char(
        string='Device Identifier for generated power',
        size=30,
    )

    generated_power_measurementid = fields.Char(
        string='Measurement Identifier for generated power',
        size=30,
    )

    generated_power_devicedesc = fields.Char(
        string='Device Description for generated power',
        size=50,
        readonly=True,
    )

    generated_power_measurementdesc = fields.Char(
        string='Measurement Description for generated power',
        size=50,
        readonly=True,
    )

    connected_to_api = fields.Boolean(
        string='Connected to API',
        default=False,
        store=True,
        compute='_compute_connected_to_api',
    )

    photovoltaicmonitoring_enabled = fields.Boolean(
        string='Photovoltaic Monitoring enabled',
        compute='_compute_photovoltaicmonitoring_enabled',
    )

    @api.depends('generated_power_deviceid',
                 'generated_power_measurementid')
    def _compute_connected_to_api(self):
        for record in self:
            connected_to_api = False
            if ((record.generated_power_deviceid or
               record.generated_power_measurementid)):
                connected_to_api = True
            record.connected_to_api = connected_to_api

    @api.multi
    def _compute_photovoltaicmonitoring_enabled(self):
        enable_photovoltaicmonitoring = self.env['ir.values'].sudo().\
            get_default('wua.infrastructure.configuration',
                        'enable_photovoltaicmonitoring')
        if enable_photovoltaicmonitoring is None:
            enable_photovoltaicmonitoring = False
        for record in self:
            record.photovoltaicmonitoring_enabled = \
                enable_photovoltaicmonitoring

    @api.model
    def create(self, vals):
        vals = self._update_vals_with_desc_fields(vals)
        return super(WuaPhotovoltaicplant, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            vals = self._update_vals_with_desc_fields(vals, True)
        return super(WuaPhotovoltaicplant, self).write(vals)

    def _update_vals_with_desc_fields(self, vals, is_write=False):
        if (('generated_power_deviceid' in vals) or
           ('generated_power_measurementid' in vals)):
            generated_power_devicedesc = ''
            generated_power_measurementdesc = ''
            generated_power_deviceid = ''
            generated_power_measurementid = ''
            if 'generated_power_deviceid' in vals:
                generated_power_deviceid = \
                    vals['generated_power_deviceid']
            if 'generated_power_measurementid' in vals:
                generated_power_measurementid = \
                    vals['generated_power_measurementid']
                if generated_power_deviceid == '' and is_write:
                    generated_power_deviceid = \
                        self.generated_power_deviceid
            desc_of_measurements = self._get_desc_of_measurements(
                [generated_power_deviceid,
                 generated_power_measurementid])
            if (desc_of_measurements and len(desc_of_measurements) == 2):
                generated_power_devicedesc = desc_of_measurements[0]
                generated_power_measurementdesc = desc_of_measurements[1]
            if 'generated_power_deviceid' in vals:
                vals['generated_power_devicedesc'] = \
                    generated_power_devicedesc
            if 'generated_power_measurementid' in vals:
                vals['generated_power_measurementdesc'] = \
                    generated_power_measurementdesc
        return vals

    # Hook
    def _get_desc_of_measurements(self, vals):
        return []

    @api.multi
    def do_get_measurements_of_photovoltaicplant(self):
        self.ensure_one()
        photovoltaicplant = self
        if (photovoltaicplant.photovoltaicmonitoring_enabled and
           photovoltaicplant.connected_to_api):
            number_of_measurements = \
                self.env['wua.photovoltaicmeasurement'].do_import_measurements(
                    photovoltaicplant.photovoltaicplant_code, False)
        message_01_ok = _('SUCCESFUL OPERATION')
        message_01_error = _('UNSUCCESSFUL OPERATION')
        message_02_ok = _('Number of measurements')
        message_02_error = _('Error in')
        message = ''
        buttons = [{'type': 'ir.actions.act_window_close',
                    'name': _('Close warning')}]
        if number_of_measurements >= 0:
            message = '<center><b>' + message_01_ok + \
                '</b></center><br><br>' + \
                message_02_ok + ': ' + \
                '<b>' + str(number_of_measurements) + '</b>'
            if number_of_measurements > 0:
                id_tree_view = self.env.ref(
                    'base_wua_pressurized_irrigation_photovoltaic_monitoring.'
                    'wua_photovoltaicmeasurement_view_tree').id
                id_form_view = self.env.ref(
                    'base_wua_pressurized_irrigation_photovoltaic_monitoring.'
                    'wua_photovoltaicmeasurement_view_form').id
                buttons.append({
                    'type': 'ir.actions.act_window',
                    'name': _('Measurements'),
                    'res_model': 'wua.photovoltaicmeasurement',
                    'view_mode': 'form',
                    'views': [[id_tree_view, 'list'],
                              [id_form_view, 'form']],
                    'domain': [('id', 'in',
                                photovoltaicplant.photovoltaicmeasurement_ids.
                                ids)],
                    'context': {'default_photovoltaicplant_id': self.id,
                                'search_default_of_active_agriculturalseason':
                                True,
                                'graph_mode': 'line'},
                    'classes': 'btn-primary'})
        else:
            message = '<center><b style="color:red;">' + \
                message_01_error + '</b></center><br><br>' + \
                message_02_error + '...  ' + \
                str(photovoltaicplant.photovoltaicplant_code) + \
                ' (' + photovoltaicplant.name + ')'
        act_window = {
            'type': 'ir.actions.act_window.message',
            'title': _('Get measurements'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': buttons}
        return act_window
