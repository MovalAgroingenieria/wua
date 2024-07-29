# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaTank(models.Model):
    _name = 'wua.tank'
    _description = 'Tank'

    MAX_SIZE_NAME = 20
    MAX_SIZE_DESCRIPTION = 75

    name = fields.Char(
        string='Tank',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        required=True,
        index=True)

    tankconsumption_ids = fields.One2many(
        string='Consumptions',
        comodel_name='wua.tankconsumption',
        inverse_name='tank_id')

    notes = fields.Html(
        string='Notes')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_tank = fields.Boolean(
        string="GIS Tank",
        readonly=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Tank.'), ]

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        tank_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_tank_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if tank_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        tank_param + '=' + \
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
    def action_see_tankconsumptions(self):
        self.ensure_one()
        condition = [('tank_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Tank consumptions'),
            'res_model': 'wua.tankconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'context': {'from_shortcut': 1},
            'target': 'current',
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
            parcel_model.create_wua_gis_tank_table()
            parcel_model.create_tank_triggers()
        except Exception:
            pass
