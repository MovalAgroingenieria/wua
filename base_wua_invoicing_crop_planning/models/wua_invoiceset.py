# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api, exceptions, _
from lxml import etree


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 9:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        enrolledsubparcel_ids = []
        for enrolledsubparcel in \
            invoiceset_line.line_enrolledsubparcel_ids.filtered(
                lambda x: x.selected is True):
            enrolledsubparcel_ids.append(
                enrolledsubparcel.enrolledsubparcel_id.id)
        return enrolledsubparcel_ids

    def get_description(self, partnerlink, enrolledsubparcel,
                        product_id, quantity):
        description = ""
        parcel_label = self.get_value_from_translation(
            'base_wua_invoicing', 'Parcel', partnerlink.partner_id.lang
        )
        parcel_code = enrolledsubparcel.parcel_id.name
        subparcel_cultivation = ""
        if(enrolledsubparcel.cultivation_id):
            subparcel_cultivation = \
                enrolledsubparcel.cultivation_id.name.lower()
        subparcel_area = ('%.4f' %
                          enrolledsubparcel.area_official).replace('.', ',')
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        area_measurement_name = ''
        if area_measurement_type == 0:
            area_measurement_name = 'ha'
        else:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
        area_measurement_name = area_measurement_name.decode('utf_8')
        profile_label = self.get_value_from_translation(
            'base_wua_invoicing_crop_planning', _('profile'),
            partnerlink.partner_id.lang
        )
        profile_name = self.get_profile_name(
            partnerlink.profile, partnerlink.partner_id.lang).lower()
        volume_label = self.get_value_from_translation(
            'base_wua_invoicing_crop_planning', _('Total vol.'),
            partnerlink.partner_id.lang)
        product = self.env['product.product'].browse(product_id)
        uom = product.uom_id.name
        contracted_volume = (
            '%.2f' % enrolledsubparcel.contracted_volume).replace('.', ',')
        costs_label = self.get_value_from_translation(
            'base_wua_invoicing_crop_planning', _('costs'),
            partnerlink.partner_id.lang
        )
        cost_percentage = '%.2f' % partnerlink.water_costs_percentage
        volume_real_label = self.get_value_from_translation(
            'base_wua_invoicing_crop_planning', _('Real vol.'),
            partnerlink.partner_id.lang
        )
        net_volume = ('%.2f' % quantity).replace('.', ',')
        description = parcel_label + ' ' + parcel_code + ', ' + \
            subparcel_cultivation + ' (' + subparcel_area + ' ' + \
            area_measurement_name + '), ' + profile_label + ': ' + \
            profile_name + "\n" + volume_label + ': ' + contracted_volume + \
            ' ' + uom + ', ' + costs_label + ': ' + cost_percentage + \
            ' %, ' + volume_real_label + ': ' + net_volume + ' ' + uom
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 9:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ09 = []
        enrolledsubparcels = self.env['wua.enrolledsubparcel'].browse(item_ids)
        for enrolledsubparcel in enrolledsubparcels:
            partnerlinks_of_parcel = partnerlinks.filtered(
                lambda x: x.parcel_id.id == enrolledsubparcel.parcel_id.id)
            for partnerlink in partnerlinks_of_parcel:
                partner_id = partnerlink.partner_id.id
                contracted_volume = enrolledsubparcel.contracted_volume
                percentage = partnerlink.water_costs_percentage
                quantity = contracted_volume * (percentage / 100)
                description = \
                    self.get_description(
                        partnerlink, enrolledsubparcel, product_id, quantity)
                result = {
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'categ_code': categ_code,
                    'key1': enrolledsubparcel.id,
                    'key2': enrolledsubparcel.parcel_id.id,
                    'quantity': quantity,
                    'description': description,
                    }
                invoice_details_categ09.append(result)
        return invoice_details_categ09

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 9:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['enrolledsubparcel_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        return data


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('enrolledsubparcel', 'Enrolled Subparcels')])

    line_enrolledsubparcel_ids = fields.One2many(
        string='Lines for enrolled subparcel',
        comodel_name='wua.invoiceset.line.enrolledsubparcel',
        inverse_name='invoicesetline_id')

    @api.depends('line_enrolledsubparcel_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'enrolledsubparcel':
                record.configured_line = \
                    len(record.line_enrolledsubparcel_ids) > 0

    def populate_items_select(self):
        if self.linkable_unit_type == 'enrolledsubparcel':
            self.populate_items_select_enrolledsubparcel(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_enrolledsubparcel(self, product_id):
        enrolledsubparcels = self.env['wua.enrolledsubparcel'].search([])
        if len(enrolledsubparcels) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_enrolledsubparcel (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, enrolledsubparcel_id,
                    parcel_id, subparcel_code, partner_id, cropplan_id,
                    subparceltype_id, area_official, cultivation_id,
                    cultivationvariety_id, profile, irrigationsystem_id,
                    productionmethod_id, hydraulicsector_id,
                    sum_price_subtotal, number_of_invoicing_processes)
                    SELECT
                    nextval('wua_invoiceset_line_enrolledsubparcel_id_seq'),
                    %s, %s, now(), now(), %s, TRUE, e.id, e.parcel_id,
                    e.subparcel_code, e.partner_id, e.cropplan_id,
                    e.subparceltype_id, e.area_official, e.cultivation_id,
                    e.cultivationvariety_id, e.profile, e.irrigationsystem_id,
                    e.productionmethod_id, e.hydraulicsector_id,
                    e.sum_price_subtotal, e.number_of_invoicing_processes
                    FROM wua_enrolledsubparcel e INNER JOIN
                    wua_agriculturalseason a ON e.agriculturalseason_id = a.id
                    WHERE e.is_validated AND a.is_the_active
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'enrolledsubparcel':
            name = _('Enrolled Subparcel')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.enrolledsubparcel'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineEnrolledsubparcel(models.Model):
    _name = 'wua.invoiceset.line.enrolledsubparcel'
    _description = 'Enrolled subparcel of a invoice-set line'
    _order = 'invoicesetline_id,enrolledsubparcel_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    enrolledsubparcel_id = fields.Many2one(
        string='Enrolled subparcel',
        comodel_name='wua.enrolledsubparcel',
        required=True,
        ondelete='restrict')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        ondelete='restrict')

    subparcel_id = fields.Many2one(
        string='Subparcel',
        comodel_name='wua.parcel.subparcel',
        ondelete='restrict')

    subparcel_code = fields.Char(
        string='Subparcel Code')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        ondelete='set null')

    subparceltype_id = fields.Many2one(
        string='Type',
        comodel_name='wua.subparceltype',
        ondelete='restrict')

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4))

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        ondelete='restrict')

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        ondelete='restrict')

    profile = fields.Selection([
        ('O', 'Owner'),
        ('L', 'Lessee'),
        ('P', 'Payer'),
        ], string='Profile')

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
        ondelete='restrict')

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    sum_price_subtotal = fields.Float(
        string='Amount')

    number_of_invoicing_processes = fields.Float(
        string='Number of invoicing processes')

    @api.depends('enrolledsubparcel_id')
    def _compute_subparcel_code(self):
        for record in self:
            record.subparcel_code = record.subparcel_code

    @api.depends('invoicesetline_id')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('invoicesetline_id')
    def _compute_number_of_invoicing_processes(self):
        for record in self:
            number_of_invoicing_processes = 0
            invoiceset_ids = []
            for invoiceline in record.invoiceline_ids:
                if (invoiceline.invoiceset_id not in invoiceset_ids):
                    number_of_invoicing_processes += 1
                    invoiceset_ids.appends(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.multi
    def add_to_invoiceset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaInvoicesetLineEnrolledsubparcel, self).fields_view_get(
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
                        'wua_invoiceset_line_enrolledsubparcel',
                        self.__class__.area_official.string)
                node.set('string',
                         original_label + ' (' + area_measurement_name + ')')
        else:
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'wua_invoiceset_line_enrolledsubparcel',
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
