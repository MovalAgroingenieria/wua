# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from operator import itemgetter


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to reset the invoiceset_id
    # and invoiced_consumption fields for the affected consumptions.
    @api.multi
    def unlink(self):
        gravconsumptions_ids = []
        for record in self:
            gravconsumptions = self.env['wua.gravconsumption'].search(
                [('invoiceset_id', '=', record.id)])
            for gravconsumption in gravconsumptions:
                gravconsumptions_ids.append(gravconsumption.id)
        res = super(WuaInvoiceset, self).unlink()
        if gravconsumptions_ids:
            gravconsumptions = self.env['wua.gravconsumption'].browse(
                gravconsumptions_ids)
            vals = {
                'invoiceset_id': None,
                'invoiced_consumption': False,
                }
            gravconsumptions.write(vals)
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 8:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        gravconsumption_ids = []
        for gravconsumption in \
            invoiceset_line.line_gravconsumption_ids.filtered(
                lambda x: x.selected is True):
            gravconsumption_ids.append(gravconsumption.gravconsumption_id.id)
        return gravconsumption_ids

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 8:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        ig_gravconsumptions = []
        gravconsumptions = self.env['wua.gravconsumption'].browse(item_ids)
        for gravconsumption in gravconsumptions:
            ig_id = gravconsumption.irrigationgate_id.id
            watering_volume_real = gravconsumption.watering_volume_real
            ig_gravconsumption = \
                filter(lambda x: x['ig_id'] == ig_id, ig_gravconsumptions)
            if not ig_gravconsumption:
                ig_gravconsumptions.append({
                    'ig_id': ig_id,
                    'watering_volume_real': watering_volume_real,
                    })
            else:
                ig_gravconsumption = ig_gravconsumption[0]
                ig_gravconsumption['watering_volume_real'] = \
                    ig_gravconsumption['watering_volume_real'] + \
                    watering_volume_real
        if len(ig_gravconsumptions) == 0:
            return []
        ig_gravconsumptions = sorted(ig_gravconsumptions,
                                     key=itemgetter('ig_id'))
        ig_ids = [x['ig_id'] for x in ig_gravconsumptions]
        invoice_details_categ08 = []
        product = self.env['product.product'].browse(product_id)
        uom = product.uom_id.name
        irrigationgates = self.env['wua.irrigationgate'].browse(ig_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'IG')])
        area_measurement_name = self.get_area_measurement_name()
        for irrigationgate in irrigationgates:
            irrigationgate_code = irrigationgate.name
            irrigationpoints_of_irrigationgate = irrigationpoints.filtered(
                lambda x: x.irrigationgate_id.id == irrigationgate.id)
            parcels_of_irrigationgate = \
                [x.parcel_id for x in irrigationpoints_of_irrigationgate
                 if x.parcel_id.is_billable_water]
            if len(parcels_of_irrigationgate) > 0:
                watering_volume_real_of_irrigationgate = \
                    filter(lambda x: x['ig_id'] ==
                           irrigationgate.id,
                           ig_gravconsumptions)[0]['watering_volume_real']
                watering_volume_real_of_irrigationgate_str = \
                    ('%.4f' % watering_volume_real_of_irrigationgate).\
                    replace('.', ',')
                total_area_official = \
                    sum(x.area_official for x in parcels_of_irrigationgate)
                for parcel in parcels_of_irrigationgate:
                    if (total_area_official == 0 or
                       watering_volume_real_of_irrigationgate == 0):
                        continue
                    gravconsumption_quantity = \
                        watering_volume_real_of_irrigationgate * \
                        (parcel.area_official / total_area_official)
                    partnerlinks_of_parcel = partnerlinks.filtered(
                        lambda x: x.parcel_id.id == parcel.id and
                        x.water_costs_percentage > 0)
                    if len(partnerlinks_of_parcel) > 0:
                        for partnerlink in partnerlinks_of_parcel:
                            partner_id = partnerlink.partner_id.id
                            profile = partnerlink.profile
                            parcel_code = parcel.name
                            area_official = parcel.area_official
                            area_official_str = ('%.4f' % area_official).\
                                replace('.', ',')
                            percentage = partnerlink.water_costs_percentage
                            percentage_str = '%.2f' % percentage
                            quantity = gravconsumption_quantity * \
                                (percentage / 100)
                            default_irrigationgate_label = \
                                _('Irrigation Gate')
                            default_parcel_label = _('Parcel')
                            default_profile_name_label = _('profile')
                            default_text01 = _('total consumption')
                            default_text02 = \
                                _('of water payment for the parcel')
                            irrigationgate_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    'Irrigation Gate',
                                    partnerlink.partner_id.lang)
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                'Parcel',
                                partnerlink.partner_id.lang)
                            profile_name_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    'profile',
                                    partnerlink.partner_id.lang)
                            profile_name = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            text01 = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                'total consumption',
                                partnerlink.partner_id.lang)
                            text02 = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                'of water payment for the parcel',
                                partnerlink.partner_id.lang)
                            if not irrigationgate_label:
                                irrigationgate_label = \
                                    default_irrigationgate_label
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            if not profile_name_label:
                                profile_name_label = \
                                    default_profile_name_label
                            if not text01:
                                text01 = default_text01
                            if not text02:
                                text02 = default_text02
                            description = parcel_label + ' ' + \
                                parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '); ' + \
                                profile_name_label + ': ' + \
                                profile_name + '\n' + \
                                irrigationgate_label + ' ' + \
                                irrigationgate_code + '; ' + \
                                text01 + ': ' + \
                                watering_volume_real_of_irrigationgate_str + \
                                ' ' + uom + '\n' + \
                                percentage_str + ' % ' + \
                                text02
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': irrigationgate.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ08.append(result)
        return invoice_details_categ08

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 8:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['irrigationgate_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        # Add overprice if there is an irrigation worker?
        overprice_with_irrigation_worker = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'overprice_with_irrigation_worker')
        if (overprice_with_irrigation_worker and
           overprice_with_irrigation_worker != 0):
            parcel = self.env['wua.parcel'].browse(data['parcel_id'])
            if parcel.with_irrigation_worker:
                data['price_unit'] = data['price_unit'] + \
                    overprice_with_irrigation_worker
        return data

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 8:
                unselected_gravconsumptions = \
                    line.line_gravconsumption_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_gravconsumptions:
                    gravconsumptions_ids = []
                    for line_gravconsumption in unselected_gravconsumptions:
                        gravconsumptions_ids.append(
                            line_gravconsumption.gravconsumption_id.id)
                    if gravconsumptions_ids:
                        gravconsumptions = \
                            self.env['wua.gravconsumption'].browse(
                                gravconsumptions_ids)
                        vals = {
                            'invoiceset_id': None,
                            'invoiced_consumption': False,
                            }
                        gravconsumptions.write(vals)
                    unselected_gravconsumptions.unlink()

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 8:
                gravconsumptions_ids = []
                for line_gravconsumption in line.line_gravconsumption_ids:
                    gravconsumptions_ids.append(
                        line_gravconsumption.gravconsumption_id.id)
                if gravconsumptions_ids:
                    gravconsumptions = self.env['wua.gravconsumption'].browse(
                        gravconsumptions_ids)
                    vals = {
                        'invoiceset_id': None,
                        'invoiced_consumption': False,
                        }
                    gravconsumptions.write(vals)
                line.line_gravconsumption_ids.unlink()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('gravconsumption', 'Gravity Consumptions')])

    line_gravconsumption_ids = fields.One2many(
        string='Lines for gravity consumptions',
        comodel_name='wua.invoiceset.line.gravconsumption',
        inverse_name='invoicesetline_id')

    @api.depends('line_gravconsumption_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'gravconsumption':
                record.configured_line = \
                    len(record.line_gravconsumption_ids) > 0

    # If a gravity-consumption line is deleted, it is necessary to reset
    # the invoiceset_id field for the affected consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            gravconsumptions_ids = []
            for line_gravconsumption in record.line_gravconsumption_ids:
                gravconsumptions_ids.append(
                    line_gravconsumption.gravconsumption_id.id)
            if gravconsumptions_ids:
                gravconsumptions = self.env['wua.gravconsumption'].browse(
                    gravconsumptions_ids)
                vals = {
                    'invoiceset_id': None,
                    'invoiced_consumption': False,
                    }
                gravconsumptions.write(vals)
        return super(WuaInvoicesetLine, self).unlink()

    def populate_items_select(self):
        if self.linkable_unit_type == 'gravconsumption':
            self.populate_items_select_gravconsumption(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_gravconsumption(self, product_id):
        gravconsumptions = self.env['wua.gravconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
        if len(gravconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_gravconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, gravconsumption_id,
                    wateringperiod_id, number, agriculturalseason_id,
                    parcel_id, subparcel_id, cadastral_reference,
                    irrigationgate_id, irrigationditch_id, watering_duration,
                    watering_id, gravconsumption_type, partner_id, vat,
                    with_irrigation_worker, employee_id, area_official,
                    watering_volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_gravconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    wateringperiod_id, number, agriculturalseason_id,
                    parcel_id, subparcel_id, cadastral_reference,
                    irrigationgate_id, irrigationditch_id, watering_duration,
                    watering_id, gravconsumption_type, partner_id, vat,
                    with_irrigation_worker, employee_id, area_official,
                    watering_volume_real
                    FROM wua_gravconsumption
                    WHERE product_id=%s and invoiceset_id is null and
                          state='executed' and watering_volume_real>0
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_gravconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null and state='executed' and
                    watering_volume_real>0""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'gravconsumption':
            name = _('Gravity Consumptions')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.gravconsumption'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineGravconsumption(models.Model):
    _name = 'wua.invoiceset.line.gravconsumption'
    _description = 'Gravity consumptions of a invoice-set line'
    _order = 'invoicesetline_id,gravconsumption_id'

    # Size of field "name".
    SIZE_CADASTRAL_REFERENCE = 14
    SIZE_VAT = 15

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    gravconsumption_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.gravconsumption',
        required=True,
        ondelete='restrict')

    wateringperiod_id = fields.Many2one(
        string='Watering Period',
        comodel_name='wua.wateringperiod',
        required=True,
        index=True,
        ondelete='restrict')

    number = fields.Integer(
        string='Number',
        required=True,
        default=1)

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        ondelete='restrict')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        ondelete='restrict')

    subparcel_id = fields.Many2one(
        string='Subparcel',
        comodel_name='wua.parcel.subparcel',
        ondelete='restrict')

    cadastral_reference = fields.Char(
        string='Cadastral Ref.',
        size=SIZE_CADASTRAL_REFERENCE)

    irrigationgate_id = fields.Many2one(
        string='Irrigation Gate',
        comodel_name='wua.irrigationgate',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    watering_duration = fields.Integer(
        string='Time (min)')

    watering_id = fields.Many2one(
        string="Watering",
        comodel_name='wua.watering',
        ondelete='restrict')

    gravconsumption_type = fields.Selection([
        ('request', 'Explicit Request'),
        ('distribution', 'Distribution'),
        ], string='Type')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    vat = fields.Char(
        string='VAT',
        size=SIZE_VAT)

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker")

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        ondelete='restrict')

    area_official = fields.Float(
        string='Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official')

    watering_volume_real = fields.Float(
        string='Total Vol. (m3)',
        digits=(32, 4))

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
