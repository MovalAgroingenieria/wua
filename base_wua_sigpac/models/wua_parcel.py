# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    sigpaclink_ids = fields.One2many(
        string='SIGPAC links',
        comodel_name='wua.parcel.sigpaclink',
        inverse_name='parcel_id')

    number_of_sigpaclinks = fields.Integer(
        string='Intersections parcel-SIGPAC enclosure',
        compute='_compute_number_of_sigpaclinks',)

    parcel_title_sigpac = fields.Char(
        string='Parcel Title for SIGPAC table',
        compute='_compute_parcel_title_sigpac')

    aerial_img_nonpersistent = fields.Binary(
        string='Aerial image, non-persistent',
        compute='_compute_aerial_img_nonpersistent')

    @api.multi
    def _compute_number_of_sigpaclinks(self):
        for record in self:
            number_of_sigpaclinks = 0
            if record.sigpaclink_ids:
                number_of_sigpaclinks = len(record.sigpaclink_ids)
            record.number_of_sigpaclinks = number_of_sigpaclinks

    @api.multi
    def _compute_parcel_title_sigpac(self):
        for record in self:
            parcel_title_sigpac = \
                _('PARCEL') + ': ' + record.name + ', ' + \
                _('SIGPAC ENCLOSURES')
            record.parcel_title_sigpac = parcel_title_sigpac

    @api.multi
    def _compute_aerial_img_nonpersistent(self):
        for record in self:
            aerial_img_nonpersistent = None
            if record.aerial_img:
                aerial_img_nonpersistent = record.aerial_img
            else:
                try:
                    record.regenerate_aerial_img()
                    aerial_img_nonpersistent = record.aerial_img
                except Exception:
                    aerial_img_nonpersistent = None
            record.aerial_img_nonpersistent = aerial_img_nonpersistent

    @api.multi
    def action_get_enclosures(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_sigpac.'
            'wua_parcel_sigpac_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('SIGPAC enclosures of the parcel'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
            }
        return act_window


class WuaParcelSigpaclink(models.Model):
    _name = 'wua.parcel.sigpaclink'
    _auto = False
    _description = 'SIGPAC link of a parcel'
    _order = 'name'

    name = fields.Char(
        string='Code of SIGPAC link',)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',)

    sigpac_id = fields.Many2one(
        string='SIGPAC Enclosure',
        comodel_name='wua.sigpac',)

    enclosure_number = fields.Integer(
        string='Enclosure Number',
        compute='_compute_enclosure_number',)

    county_id = fields.Many2one(
        string='Municipality',
        comodel_name='wua.region.state.county',)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',)

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',)

    parcel_area = fields.Float(
        string='GIS Area of parcel (m²)',
        digits=(32, 2),)

    sigpac_area = fields.Float(
        string='Area of SIGPAC enclosure (m²)',
        digits=(32, 2),)

    area_ha = fields.Float(
        string='Area (ha)',
        digits=(32, 4),)

    parcel_area_ha = fields.Float(
        string='GIS Area of parcel (ha)',
        digits=(32, 4),
        compute='_compute_parcel_area_ha',)

    intersection_percentage = fields.Float(
        string='% in parcel',
        digits=(32, 2),)

    pend_media_porc = fields.Float(
        string='Medium Slope (%)',
        digits=(32, 2),)

    coef_admis = fields.Integer(
        string='Coefficient of admissibility in pastures (0-100)',)

    coef_rega = fields.Integer(
        string='Irrigation Coefficient (0-100)',)

    uso_sigpac = fields.Selection(
        string='Land Use',
        selection=[
            ('AG', 'AG - CORRIENTES Y SUPERFICIES DE AGUA'),
            ('CA', 'CA - VIALES'),
            ('CF', 'CF - ASOCIACIÓN CÍTRICOS-FRUTALES'),
            ('CI', 'CI - CITRICOS'),
            ('CS', 'CS - ASOCIACIÓN CÍTRICOS-FRUTALES DE CÁSCARA'),
            ('CV', 'CV - ASOCIACIÓN CÍTRICOS-VIÑEDO'),
            ('ED', 'ED - EDIFICACIONES'),
            ('EP', 'EP - ELEMENTO DEL PAISAJE'),
            ('FF', 'FF - ASOCIACIÓN FRUTALES-FRUTALES DE CÁSCARA'),
            ('FL', 'FL - FRUTOS SECOS Y OLIVAR'),
            ('FO', 'FO - FORESTAL'),
            ('FS', 'FS - FRUTOS SECOS'),
            ('FV', 'FV - FRUTOS SECOS Y VIÑEDO'),
            ('FY', 'FY - FRUTALES'),
            ('IM', 'IM - IMPRODUCTIVOS'),
            ('IV', 'IV - INVERNADEROS Y CULTIVOS BAJO PLASTICO'),
            ('MT', 'MT - MATORRAL'),
            ('OC', 'OC - ASOCIACIÓN OLIVAR-CÍTRICOS'),
            ('OF', 'OF - OLIVAR - FRUTAL'),
            ('OV', 'OV - OLIVAR'),
            ('PA', 'PA - PASTO CON ARBOLADO'),
            ('PR', 'PR - PASTO ARBUSTIVO'),
            ('PS', 'PS - PASTIZAL'),
            ('TA', 'TA - TIERRAS ARABLES'),
            ('TH', 'TH - HUERTA'),
            ('VF', 'VF - VIÑEDO - FRUTAL'),
            ('VI', 'VI - VIÑEDO'),
            ('VO', 'VO - VIÑEDO - OLIVAR'),
            ('ZC', 'ZC - ZONA CONCENTRADA NO INCLUIDA EN LA ORTOFOTO'),
            ('ZU', 'ZU - ZONA URBANA'),
            ('ZV', 'ZV - ZONA CENSURADA'),
        ],)

    incidencia = fields.Char(
        string='Incidence Codes',)

    region = fields.Char(
        string='Region',)

    grp_cult = fields.Selection(
        string='Crop Group',
        selection=[
            ('CP', 'CP - Cultivos permanentes'),
            ('PT', 'PT - Pastos'),
            ('TCR', 'TCR - Tierras de cultivo de regadío'),
            ('TCS', 'TCS - Tierras de cultivo de secano'),
            ('', 'No asignado'),
        ],)

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        related='parcel_id.gis_viewer_link',)

    sigpac_link = fields.Char(
        string='SIGPAC Link',
        related='sigpac_id.sigpac_link',)

    number_of_sigpaclinks = fields.Integer(
        string='Number of associated SIGPAC enclosures of the parcel',
        related='parcel_id.number_of_sigpaclinks',)

    irrigation_model_type = fields.Integer(
        string='Irrigation Type (parameter)',
        compute='_compute_irrigation_model_type',)

    @api.multi
    def _compute_enclosure_number(self):
        for record in self:
            enclosure_number = 0
            if record.name and len(record.name) > 3:
                enclosure_number_as_str = record.name[-3:]
                if enclosure_number_as_str.isdigit():
                    enclosure_number = int(enclosure_number_as_str)
            record.enclosure_number = enclosure_number

    @api.multi
    def _compute_parcel_area_ha(self):
        for record in self:
            record.parcel_area_ha = record.parcel_area / 10000

    @api.multi
    def _compute_irrigation_model_type(self):
        irrigation_model_type = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type')
        for record in self:
            record.irrigation_model_type = irrigation_model_type

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['intersection_percentage', 'pend_media_porc',
                            'coef_rega']
        for field in fields_to_remove:
            if field in fields:
                fields.remove(field)
        return super(WuaParcelSigpaclink, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def action_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_sigpac_viewer(self):
        self.ensure_one()
        if self.sigpac_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.sigpac_link,
                'target': 'new',
            }

    @api.model
    def action_refresh_sigpac_intersections(self):
        self.sudo().env.cr.execute(
            'REFRESH MATERIALIZED VIEW CONCURRENTLY wua_parcel_sigpaclink')
