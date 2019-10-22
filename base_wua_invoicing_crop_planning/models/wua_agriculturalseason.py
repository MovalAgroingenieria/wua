# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _
from lxml import etree


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    volume_perunitarea = fields.Integer(
        string="Volumen (m3/U. Area)",
        required=True,
        default="5000")


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaAgriculturalseason, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)

        doc = etree.XML(res['arch'])

        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        area_measurement_name = ''
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode(
                'utf_8')
        if area_measurement_name != '':
            area_measurement_name = area_measurement_name.lower()
            for node in doc.xpath("//field[@name='volume_perunitarea']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'wua_agriculturalseason',
                        self.__class__.volume_perunitarea.string)
                preBar = original_label.find('/')
                if preBar != -1:
                    original_label = original_label[:preBar + 1]
                node.set('string',
                         original_label + area_measurement_name + ')')
        else:
            for node in doc.xpath("//field[@name='volume_perunitarea']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'wua_agriculturalseason',
                        self.__class__.volume_perunitarea.string)
                preBar = original_label.find('/')
                if preBar != -1:
                    original_label = original_label[:preBar + 1]
                node.set('string', original_label + _('hectares') + ')')
        res['arch'] = etree.tostring(doc)
        return res

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp
