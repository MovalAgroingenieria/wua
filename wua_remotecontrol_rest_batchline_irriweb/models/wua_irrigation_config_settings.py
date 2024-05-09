# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_batchline = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_batchline = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_batchline = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_batchline = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_batchline = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_batchline = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_batchline = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_batchline = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_batchline = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_batchline = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_batchline = fields.Boolean(
        string='Import from hydraulic sector')

    import_irrigation_schedule_from_waterconnections_batchline = \
        fields.Boolean(
            string='Import Irrigation Schedule from waterconnection')

    php_frame_enabled = fields.Boolean(
        string='PHP (frames)',
        default=False)

    php_frame_url = fields.Char(
        string='PHP (frames), URL',
        size=255)

    php_frame_type_historico = fields.Char(
        string='PHP (frames), readings',
        size=50,
        help='For build a PHP url that gives the readings. ' +
             'Example: http://78.136.122.3:8080/demo/baja/historico.php')

    php_frame_type_historico_width = fields.Integer(
        string='PHP (frames), readings width')

    php_frame_type_historico_height = fields.Integer(
        string='PHP (frames), readings height')

    php_frame_type_consumo = fields.Char(
        string='PHP (frames), consumptions',
        size=50,
        help='For build a PHP url that gives the consumptions. ' +
             'Example: http://78.136.122.3:8080/demo/baja/consumo.php')

    php_frame_type_consumo_width = fields.Integer(
        string='PHP (frames), consumptions width')

    php_frame_type_consumo_height = fields.Integer(
        string='PHP (frames), consumptions height')

    php_frame_type_programacion = fields.Char(
        string='PHP (frames), scheduling',
        size=50,
        help='For build a PHP url that gives the scheduling of ' +
             'water connections. Example: ' +
             'http://78.136.122.3:8080/demo/baja/programacion.php')

    php_frame_type_programacion_width = fields.Integer(
        string='PHP (frames), scheduling width')

    php_frame_type_programacion_height = fields.Integer(
        string='PHP (frames), scheduling height')

    php_frame_client = fields.Char(
        string='PHP (frames), \"client\" parameter',
        size=50)

    php_frame_accesskey = fields.Char(
        string='PHP (frames), \"accesskey\" parameter',
        size=100)

    php_frame_secretkey = fields.Char(
        string='PHP (frames), \"secretkey\" parameter',
        size=100)

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_batchline',
                           self.url_remotecontrol_rest_batchline)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_batchline',
                           self.url_remotecontrol_rest_username_batchline)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_batchline',
                           self.url_remotecontrol_rest_password_batchline)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_batchline',
                           self.url_remotecontrol_application_batchline)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_batchline',
                           self.automatic_census_synchronization_batchline)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_enabled',
                           self.php_frame_enabled)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_url',
                           self.php_frame_url)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_historico',
                           self.php_frame_type_historico)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_historico_width',
                           self.php_frame_type_historico_width)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_historico_height',
                           self.php_frame_type_historico_height)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_consumo',
                           self.php_frame_type_consumo)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_consumo_width',
                           self.php_frame_type_consumo_width)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_consumo_height',
                           self.php_frame_type_consumo_height)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_programacion',
                           self.php_frame_type_programacion)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_programacion_width',
                           self.php_frame_type_programacion_width)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_programacion_height',
                           self.php_frame_type_programacion_height)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_client',
                           self.php_frame_client)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_accesskey',
                           self.php_frame_accesskey)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_secretkey',
                           self.php_frame_secretkey)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET batchline config
        batchline_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_batchline')
        return other_can_send or batchline_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET batchline config
        batchline_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_batchline')
        return other_can_send or batchline_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET batchline config
        batchline_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_batchline')
        return other_can_import or batchline_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET batchline config
        batchline_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_batchline')
        return other_can_import or batchline_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET batchline config
        batchline_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_batchline')
        return other_can_import or batchline_can_impport

    def import_irrigation_schedule_from_wc_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_irrigation_schedule_from_wc_any()
        # GET inelcom config
        batchline_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_irrigation_schedule_from_waterconnections_batchline')
        return other_can_import or batchline_can_impport
