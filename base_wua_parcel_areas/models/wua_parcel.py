# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from lxml import etree


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    area_irrigation_percentage = fields.Float(
        string='Irrigation %',
        digits=(5, 2),
        default=100,
        index=True)

    area_irrigation = fields.Float(
        string='Irrigation Area',
        digits=(32, 4),
        index=True,
        store=True,
        compute='_compute_irrigation_area')

    area_unproductive_percentage = fields.Float(
        string='Unproductive %',
        digits=(5, 2),
        default=0,
        index=True)

    area_unproductive = fields.Float(
        string='Unproductive Area',
        digits=(32, 4),
        index=True,
        store=True,
        compute='_compute_unproductive_area')

    area_drainage_percentage = fields.Float(
        string='Drainage %',
        digits=(5, 2),
        default=100,
        index=True)

    area_drainage = fields.Float(
        string='Drainage Area',
        digits=(32, 4),
        index=True,
        store=True,
        compute='_compute_drainage_area')

    billable_irrigation_percentage = fields.Boolean(
        string='Billable Irrigation %',
        default=True)

    _sql_constraints = [
        ('valid_area_irrigation_percentage',
         'CHECK (area_irrigation_percentage BETWEEN 0 AND 100)',
         'The irrigation percentage must be a value between 0 and 100.'),
        ('valid_area_unproductive_percentage',
         'CHECK (area_unproductive_percentage BETWEEN 0 AND 100)',
         'The unproductive percentage must be a value between 0 and 100.'),
        ('valid_area_drainage_percentage',
         'CHECK (area_drainage_percentage BETWEEN 0 AND 100)',
         'The drainage percentage must be a value between 0 and 100.'),
        ('valid_sum_percentage_areas_irrigation_unproductive',
         'CHECK (area_irrigation_percentage + \
                 area_unproductive_percentage = 100)',
         'The sum of the percentage of the irrigation and \
          unproductive areas must be 100.'),
        ]

    @api.depends('area_official', 'area_irrigation_percentage')
    def _compute_irrigation_area(self):
        for record in self:
            record.area_irrigation = (
                record.area_official *
                record.area_irrigation_percentage) / 100

    @api.depends('area_official', 'area_unproductive_percentage')
    def _compute_unproductive_area(self):
        for record in self:
            record.area_unproductive = (
                record.area_official *
                record.area_unproductive_percentage) / 100

    @api.depends('area_official', 'area_drainage_percentage')
    def _compute_drainage_area(self):
        for record in self:
            record.area_drainage = (
                record.area_official *
                record.area_drainage_percentage) / 100

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcel, self).fields_view_get(view_id=view_id,
                                                     view_type=view_type,
                                                     toolbar=toolbar,
                                                     submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            else:
                if view_type == 'form':
                    for node in doc.xpath("//field[@name='area_irrigation']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_irrigation.string)
                        node.set('string', original_label +
                                 ' (' + _('hectares') + ')')
                    for node in doc.xpath(
                                    "//field[@name='area_unproductive']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_unproductive.string)
                        node.set('string', original_label +
                                 ' (' + _('hectares') + ')')
                    for node in doc.xpath("//field[@name='area_drainage']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_drainage.string)
                        node.set('string', original_label +
                                 ' (' + _('hectares') + ')')
                for node in doc.xpath("//field[@name='area_irrigation']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_irrigation.string)
                    node.set('string', original_label +
                             ' (' + _('hectares') + ')')
                for node in doc.xpath("//field[@name='area_unproductive']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_unproductive.string)
                    node.set('string', original_label +
                             ' (' + _('hectares') + ')')
                for node in doc.xpath("//field[@name='area_drainage']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_drainage.string)
                    node.set('string', original_label +
                             ' (' + _('hectares') + ')')
            if area_measurement_name != '':
                area_measurement_name = ' (' + \
                    area_measurement_name.lower() + ')'
                if view_type == 'form':
                    for node in doc.xpath("//field[@name='area_irrigation']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_irrigation.string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string', original_label +
                                 area_measurement_name)
                    for node in doc.xpath(
                                    "//field[@name='area_unproductive']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_unproductive.string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string', original_label +
                                 area_measurement_name)
                    for node in doc.xpath("//field[@name='area_drainage']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua_parcel_areas',
                                self.__class__.area_drainage.string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string', original_label +
                                 area_measurement_name)
                for node in doc.xpath("//field[@name='area_irrigation']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_irrigation.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
                for node in doc.xpath("//field[@name='area_unproductive']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_irrigation.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
                for node in doc.xpath("//field[@name='area_drainage']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua_parcel_areas',
                            self.__class__.area_drainage.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
            res['arch'] = etree.tostring(doc)
        return res
