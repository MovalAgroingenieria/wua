# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from lxml import etree


class WuaCropplan(models.Model):
    _inherit = 'wua.cropplan'

    contracted_volume = fields.Float(
        string='Contracted Water (m3)',
        store=True,
        index=True,
        compute='_compute_contracted_volume'
    )

    @api.depends('enrolledsubparcel_ids',
                 'enrolledsubparcel_ids.contracted_volume')
    def _compute_contracted_volume(self):
        for record in self:
            total_volume = 0
            if (record.enrolledsubparcel_ids):
                for enrolledsubparcel in record.enrolledsubparcel_ids:
                    if (enrolledsubparcel.contracted_volume):
                        total_volume += enrolledsubparcel.contracted_volume
            record.contracted_volume = total_volume

    @api.multi
    def cancel_cropplan(self):
        for enrolledsubparcel in self.enrolledsubparcel_ids:
            if enrolledsubparcel.invoiced:
                raise exceptions.ValidationError(_('The cultivation plan '
                                                   'cannot be canceled, '
                                                   'there is at least one'
                                                   'subparcel that has '
                                                   'already been invoiced.'))
            super(WuaCropplan, self).cancel_cropplan()


class WuaEnrolledsubparcel(models.Model):
    _inherit = 'wua.enrolledsubparcel'

    contracted_volume = fields.Float(
        string='Contracted Water (m3)',
        store=True,
        index=True,
        compute='_compute_contracted_volume'
    )

    invoiceline_ids = fields.One2many(
        string='Invoice Lines',
        comodel_name='account.invoice.line',
        inverse_name='enrolledsubparcel_id'
    )

    sum_price_subtotal = fields.Float(
        string='Amount',
        store=True,
        index=True,
        compute='_compute_sum_price_subtotal'
    )

    number_of_invoicing_processes = fields.Float(
        string='Number of invoicing processes',
        store=True,
        index=True,
        compute='_compute_number_of_invoicing_processes'
    )

    invoiced = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced'
    )

    is_validated = fields.Boolean(
        string='Validated',
        store=True,
        index=True,
        compute='_compute_validated')

    @api.depends('area_official', 'agriculturalseason_id.volume_perunitarea')
    def _compute_contracted_volume(self):
        for record in self:
            contracted_volume = 0
            if (record.agriculturalseason_id.volume_perunitarea):
                contracted_volume = record.area_official * \
                    record.agriculturalseason_id.volume_perunitarea
            record.contracted_volume = contracted_volume

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.price_subtotal')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('invoiceline_ids')
    def _compute_number_of_invoicing_processes(self):
        for record in self:
            number_of_invoicing_processes = 0
            invoiceset_ids = []
            for invoiceline in record.invoiceline_ids:
                if (invoiceline.invoiceset_id not in invoiceset_ids):
                    number_of_invoicing_processes += 1
                    invoiceset_ids.append(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.depends('number_of_invoicing_processes')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = record.number_of_invoicing_processes > 0

    @api.depends('cropplan_id.state')
    def _compute_validated(self):
        for record in self:
            if record.cropplan_id.state == 'validated':
                record.is_validated = True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaEnrolledsubparcel, self).fields_view_get(
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
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'wua.enrolledsubparcel',
                        self.__class__.area_official.string)
                node.set('string',
                         original_label + ' (' + area_measurement_name + ')')
        else:
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'wua.enrolledsubparcel',
                        self.__class__.area_official.string)
                node.set('string', original_label + ' (' + _('hectares') + ')')
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
