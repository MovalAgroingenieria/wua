# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from operator import itemgetter
from odoo import models, fields, api, exceptions, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to reset the invoiceset_id
    # and invoiced_consumption fields for the affected consumptions.
    @api.multi
    def unlink(self):
        fertconsumptions_ids = []
        for record in self:
            fertconsumptions = self.env['wua.fertconsumption'].search(
                [('invoiceset_id', '=', record.id)])
            for fertconsumption in fertconsumptions:
                fertconsumptions_ids.append(fertconsumption.id)
        res = super(WuaInvoiceset, self).unlink()
        if fertconsumptions_ids:
            fertconsumptions = self.env['wua.fertconsumption'].browse(
                fertconsumptions_ids)
            vals = {
                'invoiceset_id': None,
                'invoiced_consumption': False,
                }
            fertconsumptions.write(vals)
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 12:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        fertconsumption_ids = []
        for fertconsumption in \
            invoiceset_line.line_fertconsumption_ids.filtered(
                lambda x: x.selected is True):
            fertconsumption_ids.append(fertconsumption.fertconsumption_id.id)
        return fertconsumption_ids

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 12:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        wc_no_irrigationpoints = \
            self.get_wc_no_irrigationpoints_fertconsumption(item_ids)
        if wc_no_irrigationpoints:
            message_wc_no_irrigationpoints = \
                _('It is not possible to generate invoices. The following '
                  'water connections do not have irrigation points (and, '
                  'therefore, their consumptions cannot be invoiced)')
            raise exceptions.UserError(
                message_wc_no_irrigationpoints + ': ' +
                wc_no_irrigationpoints)
        if (self.env['ir.values'].get_default(
           'wua.invoicing.configuration', 'invoicing_based_on_wc')):
            return self.calculate_invoice_details_categ12_based_on_wc(
                product_id, categ_code, item_ids, partnerlinks)
        else:
            return self.calculate_invoice_details_categ12_normal(
                product_id, categ_code, item_ids, partnerlinks)

    def get_wc_no_irrigationpoints_fertconsumption(self, fertconsumption_ids):
        resp = ''
        wc_ids = []
        fertconsumptions = self.env['wua.fertconsumption'].browse(
            fertconsumption_ids)
        for fertconsumption in (fertconsumptions or []):
            wc_ids.append(fertconsumption.waterconnection_id.id)
        if len(wc_ids) > 0:
            wc_ids = sorted(list(set(wc_ids)))
            waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
            for waterconnection in waterconnections:
                if not waterconnection.irrigationpoint_ids:
                    resp = resp + ', ' + waterconnection.name
            if resp:
                resp = resp[2:]
        return resp

    def calculate_invoice_details_categ12_normal(
            self, product_id, categ_code, item_ids, partnerlinks):
        wc_fertconsumptions = []
        fertconsumptions = self.env['wua.fertconsumption'].browse(item_ids)
        for fertconsumption in fertconsumptions:
            wc_id = fertconsumption.waterconnection_id.id
            amount = fertconsumption.amount
            wc_fertconsumption = \
                filter(lambda x: x['wc_id'] == wc_id, wc_fertconsumptions)
            if not wc_fertconsumption:
                wc_fertconsumptions.append({
                    'wc_id': wc_id,
                    'amount': amount,
                    })
            else:
                wc_fertconsumption = wc_fertconsumption[0]
                wc_fertconsumption['amount'] = \
                    wc_fertconsumption['amount'] + amount
        if len(wc_fertconsumptions) == 0:
            return []
        wc_fertconsumptions = sorted(wc_fertconsumptions,
                                     key=itemgetter('wc_id'))
        wc_ids = [x['wc_id'] for x in wc_fertconsumptions]
        invoice_details_categ12 = []
        product = self.env['product.product'].browse(product_id)
        uom = product.uom_id.name
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        area_measurement_name = self.get_area_measurement_name()
        for waterconnection in waterconnections:
            waterconnection_code = waterconnection.name
            irrigationpoints_of_waterconnection = irrigationpoints.filtered(
                lambda x: x.waterconnection_id.id == waterconnection.id)
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            if len(parcels_of_waterconnection) > 0:
                amount_of_waterconnection = \
                    filter(lambda x: x['wc_id'] ==
                           waterconnection.id,
                           wc_fertconsumptions)[0]['amount']
                amount_of_waterconnection_str = \
                    ('%.4f' % amount_of_waterconnection).\
                    replace('.', ',')
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                for parcel in parcels_of_waterconnection:
                    if (total_area_official == 0 or
                       amount_of_waterconnection == 0):
                        continue
                    fertconsumption_quantity = \
                        amount_of_waterconnection * \
                        (parcel.area_official / total_area_official)
                    fertconsumption_percentage = \
                        (100 * fertconsumption_quantity /
                         amount_of_waterconnection)
                    fertconsumption_percentage_str = \
                        '%.2f' % fertconsumption_percentage
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
                            quantity = fertconsumption_quantity * \
                                (percentage / 100)
                            quantity_str = ('%.4f' % quantity).\
                                replace('.', ',')
                            default_waterconnection_label = \
                                _('Water Connection')
                            default_parcel_label = _('Parcel')
                            default_profile_name_label = _('profile')
                            default_text01 = _('total consumption')
                            default_text02 = \
                                _('of total consumption of water meter')
                            default_text03 = \
                                _('of water payment for the parcel')
                            waterconnection_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'pressurized_irrigation',
                                    'Water Connection',
                                    partnerlink.partner_id.lang)
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'Parcel',
                                partnerlink.partner_id.lang)
                            profile_name_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'pressurized_irrigation',
                                    'profile',
                                    partnerlink.partner_id.lang)
                            profile_name = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            text01 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'total consumption',
                                partnerlink.partner_id.lang)
                            text02 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'of total consumption of water meter',
                                partnerlink.partner_id.lang)
                            text03 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'of water payment for the parcel',
                                partnerlink.partner_id.lang)
                            if not waterconnection_label:
                                waterconnection_label = \
                                    default_waterconnection_label
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            if not profile_name_label:
                                profile_name_label = \
                                    default_profile_name_label
                            if not text01:
                                text01 = default_text01
                            if not text02:
                                text02 = default_text02
                            if not text03:
                                text03 = default_text03
                            description = parcel_label + ' ' + \
                                parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '); ' + \
                                profile_name_label + ': ' + \
                                profile_name + '\n' + \
                                waterconnection_label + ' ' + \
                                waterconnection_code + '; ' + \
                                text01 + ': ' + \
                                amount_of_waterconnection_str + \
                                ' ' + uom + '\n' + \
                                fertconsumption_percentage_str + ' % ' + \
                                text02 + \
                                ' (' + quantity_str + ' ' + uom + ')\n' + \
                                percentage_str + ' % ' + \
                                text03
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': waterconnection.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ12.append(result)
        return invoice_details_categ12

    def calculate_invoice_details_categ12_based_on_wc(
            self, product_id, categ_code, item_ids, partnerlinks):
        wc_ids = []
        fertconsumptions = self.env['wua.fertconsumption'].browse(item_ids)
        for fertconsumption in fertconsumptions:
            wc_ids.append(fertconsumption.waterconnection_id.id)
        if len(wc_ids) == 0:
            return []
        wc_ids = sorted(list(set(wc_ids)))
        invoice_details_categ12 = []
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        # For each water connection: all parcels of this water connection
        # must have the same water payer.
        wc_partners = []
        for waterconnection in waterconnections:
            irrigationpoints_of_waterconnection = irrigationpoints.filtered(
                lambda x: x.waterconnection_id.id == waterconnection.id)
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            first_partnerlink = True
            partner_of_wc_id = 0
            for parcel in parcels_of_waterconnection:
                partnerlinks_of_parcel = partnerlinks.filtered(
                    lambda x: x.parcel_id.id == parcel.id and
                    x.water_costs_percentage > 0)
                for partnerlink in partnerlinks_of_parcel:
                    if first_partnerlink:
                        partner_of_wc_id = partnerlink.partner_id.id
                        first_partnerlink = False
                        wc_partners.append({
                            'wc_id': waterconnection.id,
                            'partner_id': partner_of_wc_id,
                            })
                    else:
                        if partnerlink.partner_id.id != partner_of_wc_id:
                            message_wc_more_one_water_payer_01 = \
                                _('It is not possible to generate invoices. '
                                  'Check the census: the parcels of water '
                                  'connection')
                            message_wc_more_one_water_payer_02 = \
                                _('do not have the same water payer.')
                            raise exceptions.UserError(
                                message_wc_more_one_water_payer_01 + ' ' +
                                waterconnection.name + ' ' +
                                message_wc_more_one_water_payer_02)
        # Loop on fertilizer consumptions to generate the invoice lines.
        for fertconsumption in fertconsumptions:
            waterconnection = fertconsumption.waterconnection_id
            filtered_partner = \
                filter(lambda x: x['wc_id'] == waterconnection.id, wc_partners)
            if filtered_partner:
                partner_id = filtered_partner[0]['partner_id']
                description = self.get_detail_of_fertconsumption(
                    fertconsumption, partner_id)
                result = {
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'categ_code': categ_code,
                    'key1': waterconnection.id,
                    'quantity': fertconsumption.amount,
                    'description': description,
                    }
                invoice_details_categ12.append(result)
        return invoice_details_categ12

    def get_detail_of_fertconsumption(self, fertconsumption, partner_id):
        resp = ''
        lang = self.env['res.partner'].browse(partner_id).lang
        default_waterconnection_label = _('Water Connection')
        waterconnection_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'Water Connection', lang)
        if not waterconnection_label:
            waterconnection_label = default_waterconnection_label
        resp = waterconnection_label + ' ' + \
            fertconsumption.waterconnection_id.name + ' ' + '[' + \
            fertconsumption.product_id.name + ']'
        return resp

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 12:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['waterconnection_id'] = invoice_data_line['key1']
        if 'key2' in invoice_data_line:
            data['parcel_id'] = invoice_data_line['key2']
        return data

    # If invoicing based on wc, fertconsumption on same griup as
    # presconsumption
    def get_invoice_details_to_group(self, invoice_details):
        invoice_details_to_group = super(WuaInvoiceset, self).\
            get_invoice_details_to_group(invoice_details)
        invoicing_based_on_wc = self.env['ir.values'].\
            get_default('wua.invoicing.configuration', 'invoicing_based_on_wc')
        invoice_details_categ7 = filter(
            lambda x: x['categ_code'] in [12],
            invoice_details)
        if (invoicing_based_on_wc and invoice_details_categ7):
            invoice_details_to_group = invoice_details_to_group + \
                invoice_details_categ7
        return invoice_details_to_group

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 12:
                unselected_fertconsumptions = \
                    line.line_fertconsumption_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_fertconsumptions:
                    fertconsumptions_ids = []
                    for line_fertconsumption in unselected_fertconsumptions:
                        fertconsumptions_ids.append(
                            line_fertconsumption.fertconsumption_id.id)
                    if fertconsumptions_ids:
                        fertconsumptions = \
                            self.env['wua.fertconsumption'].browse(
                                fertconsumptions_ids)
                        vals = {
                            'invoiceset_id': None,
                            'invoiced_consumption': False,
                            }
                        fertconsumptions.write(vals)
                    unselected_fertconsumptions.unlink()

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 12:
                fertconsumptions_ids = []
                for line_fertconsumption in line.line_fertconsumption_ids:
                    fertconsumptions_ids.append(
                        line_fertconsumption.fertconsumption_id.id)
                if fertconsumptions_ids:
                    fertconsumptions = self.env['wua.fertconsumption'].browse(
                        fertconsumptions_ids)
                    vals = {
                        'invoiceset_id': None,
                        'invoiced_consumption': False,
                        }
                    fertconsumptions.write(vals)
                line.line_fertconsumption_ids.unlink()

    def group_invoice_details_by_wc(self, invoice_details):
        invoices_data = []
        wc_ids = []
        for item in invoice_details:
            wc_ids.append(item['key1'])
        wc_ids = sorted(list(set(wc_ids)))
        waterconnections = \
            self.env['wua.waterconnection'].browse(wc_ids).sorted(
                key=lambda x: x.name)
        for waterconnection in waterconnections:
            invoice_details_of_wc = filter(
                lambda x: x['key1'] == waterconnection.id, invoice_details)
            if waterconnection.watercosts_separate_billing:
                for invoice_detail in invoice_details_of_wc:
                    invoice_detail['payment_mode_id'] = \
                        waterconnection.watercosts_payment_mode_id.id
                    if waterconnection.watercosts_mandate_required:
                        invoice_detail['mandate_id'] = \
                            waterconnection.watercosts_mandate_id.id
            partner = self.env['res.partner'].browse(
                invoice_details_of_wc[0]['partner_id'])
            result = {
                'partner_id': partner.id,
                'partner_code': partner.partner_code,
                'account_id': partner.property_account_receivable_id.id,
                'payment_term_id': partner.property_payment_term_id.id,
                'payment_mode_id': partner.customer_payment_mode_id.id,
                'customer_invoice_transmit_method_id':
                    partner.customer_invoice_transmit_method_id.id,
                'detail': invoice_details_of_wc,
                }
            invoices_data.append(result)
        return invoices_data


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('fertconsumption', 'Fertilizer Consumptions')])

    line_fertconsumption_ids = fields.One2many(
        string='Selected items for invoice-set line',
        comodel_name='wua.invoiceset.line.fertconsumption',
        inverse_name='invoicesetline_id')

    @api.depends('line_fertconsumption_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'fertconsumption':
                record.configured_line = \
                    len(record.line_fertconsumption_ids) > 0

    # If a fertilizer-consumption line is deleted, it is necessary to reset
    # the invoiceset_id field for the affected consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            fertconsumptions_ids = []
            for line_fertconsumption in record.line_fertconsumption_ids:
                fertconsumptions_ids.append(
                    line_fertconsumption.fertconsumption_id.id)
            if fertconsumptions_ids:
                fertconsumptions = self.env['wua.fertconsumption'].browse(
                    fertconsumptions_ids)
                vals = {
                    'invoiceset_id': None,
                    'invoiced_consumption': False,
                    }
                fertconsumptions.write(vals)
        return super(WuaInvoicesetLine, self).unlink()

    def populate_items_select(self):
        if self.linkable_unit_type == 'fertconsumption':
            self.populate_items_select_fertconsumption(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_fertconsumption(self, product_id):
        fertconsumptions = self.env['wua.fertconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
        if len(fertconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_fertconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, fertconsumption_id,
                    reading_initial_time,
                    reading_end_time,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    amount)
                    SELECT
                    nextval('wua_invoiceset_line_fertconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    reading_initial_time,
                    reading_end_time,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    amount
                    FROM wua_fertconsumption
                    WHERE product_id=%s and invoiceset_id is null
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_fertconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'fertconsumption':
            name = _('Fertilizer Consumptions')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.fertconsumption'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineFertconsumption(models.Model):
    _name = 'wua.invoiceset.line.fertconsumption'
    _description = 'Fertilizer consumptions of a invoice-set line'
    _order = 'invoicesetline_id,fertconsumption_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    fertconsumption_id = fields.Many2one(
        string='Fertilized Consumption',
        comodel_name='wua.fertconsumption',
        required=True,
        ondelete='restrict')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    reading_initial_time = fields.Datetime(
        string='Reading Start Time')

    reading_end_time = fields.Datetime(
        string='Reading End Time')

    amount = fields.Float(
        string='Amount',
        digits=(32, 4), default=0)

    uom_id = fields.Many2one(
        string='Unit of measure',
        comodel_name='product.uom',
        ondelete='restrict')

    with_presconsumption = fields.Boolean(
        string='Water Consumption')

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
