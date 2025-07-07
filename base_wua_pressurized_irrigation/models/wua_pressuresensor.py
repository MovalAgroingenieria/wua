# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPressuresensor(models.Model):
    _name = 'wua.pressuresensor'
    _description = 'Entity (pressure sensor)'
    _order = 'name'

    name = fields.Char(
        string='Name',
        size=50,
        required=True,
        index=True,)

    description = fields.Char(
        string='Description',
        index=True,)

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='restrict',)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulicsector_id',
        ondelete='restrict',)

    notes = fields.Html(
        string='Notes',)

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',)

    with_gis_pressuresensor = fields.Boolean(
        string='GIS Pressure Sensor',)

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame',)

    pressuresensormeasurement_ids = fields.One2many(
        string='Measurements',
        comodel_name='wua.pressuresensormeasurement',
        inverse_name='pressuresensor_id')

    number_of_measurements = fields.Integer(
        string='N. of measurements',
        compute='_compute_number_of_measurements')

    last_measurement_time = fields.Datetime(
        string="Last measurement",
        compute='_compute_last_measurement')

    last_measurement_pressure = fields.Float(
        string="Last measurement pressure (bar)",
        digits=(32, 2),
        compute="_compute_last_measurement")

    serial_number = fields.Char(
        size=40,
        string="Serial Number",
        index=True,
        track_visibility='onchange',
    )

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
    ]

    @api.depends('irrigationshed_id', 'irrigationshed_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if record.irrigationshed_id:
                hydraulicsector_id = record.irrigationshed_id.\
                    hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        pressuresensor_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_pressuresensor_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if pressuresensor_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        pressuresensor_param + '=' + \
                        str(record.name)
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if (cipher_text):
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            if record.with_gis_pressuresensor and record.gis_viewer_link != '':
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:0px;' + \
                    'margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_pressuresensors" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="0" height="260" width="98%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''

    @api.multi
    def _compute_number_of_measurements(self):
        for record in self:
            number_of_measurements = 0
            self.env.cr.execute("""
                SELECT count(*) FROM wua_pressuresensormeasurement
                WHERE pressuresensor_id=""" + str(record.id) + """""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('count') is not None):
                number_of_measurements = \
                    query_results[0].get('count')
            record.number_of_measurements = number_of_measurements

    @api.multi
    def _compute_last_measurement(self):
        for record in self:
            last_measurement_time = None
            last_measurement_pressure = 0
            self.env.cr.execute("""
                SELECT measurement_time, pressure
                FROM wua_pressuresensormeasurement
                WHERE pressuresensor_id=""" + str(record.id) + """
                ORDER BY measurement_time DESC
                LIMIT 1""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('measurement_time') is not None):
                last_measurement_time = \
                    query_results[0].get('measurement_time')
                last_measurement_pressure = \
                    query_results[0].get('pressure')
            record.last_measurement_time = last_measurement_time
            record.last_measurement_pressure = \
                last_measurement_pressure

    @api.multi
    def action_show_pressuresensormeasurements(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_pressuresensormeasurement_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_pressuresensormeasurement_view_form').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_pressuresensormeasurement_view_search')
        id_graph_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_pressuresensormeasurement_view_graph').id
        id_pivot_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_pressuresensormeasurement_view_pivot').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Measurements'),
            'res_model': 'wua.pressuresensormeasurement',
            'view_type': 'form',
            'view_mode': 'tree,graph,pivot',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_graph_view, 'graph'), (id_pivot_view, 'pivot')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.pressuresensormeasurement_ids.ids)],
            'context': {'default_pressuresensor_id': self.id,
                        'search_default_of_active_agriculturalseason': True,
                        "graph_mode": "line",
                        'from_shortcut': 1, },
            }
        return act_window

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_pressuresensor_table()
            parcel_model.create_pressuresensor_triggers()
        except Exception:
            pass
