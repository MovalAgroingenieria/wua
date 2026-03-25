# -*- coding: utf-8 -*-
# Cpyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def _update_hmovement_invoice_status(self, hydricmovement_ids):
        if (hydricmovement_ids):
            try:
                hydricmovement_ids = tuple(hydricmovement_ids)
                # hmov invoiced if some invoice_line
                query_update_invoiced = """
                    UPDATE wua_hydricmovement wh1
                    SET invoiced_hydricmovement = CASE
                        WHEN EXISTS (
                            SELECT 1 FROM account_invoice_line ail
                            WHERE ail.hydricmovement_id = wh1.id
                        ) THEN TRUE
                        ELSE FALSE
                    END
                    WHERE wh1.id IN %s
                """
                self.env.cr.execute(
                    query_update_invoiced, (hydricmovement_ids,))
                # hmov invoiceset_id = the last invoice
                query_update_invoiceset_id = """
                    UPDATE wua_hydricmovement wh1
                    SET invoiceset_id = a.max_invoiceset_id
                    FROM (
                        SELECT ail.hydricmovement_id AS hydricmovement_id,
                            MAX(ail.invoiceset_id) AS max_invoiceset_id
                        FROM account_invoice_line ail
                        WHERE ail.hydricmovement_id IN %s
                        GROUP BY ail.hydricmovement_id
                    ) AS a
                    WHERE wh1.id = a.hydricmovement_id
                """
                self.env.cr.execute(
                    query_update_invoiceset_id, (hydricmovement_ids,))
                # presconsumption invoiced if some invoiced_hydricmovement
                query_update_presconsumption = """
                    UPDATE wua_presconsumption wp1
                    SET invoiced_consumption_quota =
                        a.has_invoiced_hydricmovement
                    FROM (
                        SELECT
                            wh1.presconsumption_id,
                            CASE WHEN COUNT(*) > 0 THEN TRUE ELSE FALSE END AS
                                has_invoiced_hydricmovement
                        FROM wua_hydricmovement wh1
                        WHERE wh1.id IN %s AND wh1.invoiced_hydricmovement
                        GROUP BY wh1.presconsumption_id
                    ) AS a
                    WHERE wp1.id = a.presconsumption_id
                """
                self.env.cr.execute(
                    query_update_presconsumption, (hydricmovement_ids,))
                # TODO: This is updating all readings, not only the ones
                # related to the hydricmovements in hydricmovement_ids we
                # should filter the readings to update only the ones related
                query_update_reading = """
                    UPDATE wua_reading wr1
                    SET invoiced_reading_quota = TRUE
                    FROM wua_presconsumption wp1
                    WHERE wr1.presconsumption_id = wp1.id
                    AND wp1.invoiced_consumption_quota
                """
                self.env.cr.execute(query_update_reading)
                # irrigationreport invoiced if some = the last invoice
                query_update_irrigationreport = """
                    UPDATE wua_irrigationreport wi1
                    SET invoiced_irrigationreport_quota =
                        a.has_invoiced_hydricmovement
                    FROM (
                        SELECT
                            wh1.irrigationreport_id,
                            CASE WHEN COUNT(*) > 0 THEN TRUE ELSE FALSE END AS
                                has_invoiced_hydricmovement
                        FROM wua_hydricmovement wh1
                        WHERE wh1.id IN %s AND wh1.invoiced_hydricmovement
                        GROUP BY wh1.irrigationreport_id
                    ) AS a
                    WHERE wi1.id = a.irrigationreport_id
                """
                self.env.cr.execute(
                    query_update_irrigationreport, (hydricmovement_ids,))
            except Exception as e:
                raise ValidationError(_(
                    'Error when updating hydric movement '
                    'invoice info: {}'.format(e)))

    # If a invoice set is deleted, it is necessary to make the hydricmovement
    # selectable again by setting it as not invoiced and remove the invoceset
    # associated. The pres_consumptions marked as invoiced by quota have to
    # set as not invoiced too
    @api.multi
    def unlink(self):
        hydricmovement_ids = []
        quota_pres_consumption_ids = []
        quota_irrigationreport_ids = []
        if self.ids:
            hydricmovements = self.env['wua.hydricmovement'].search(
                [('invoiceset_id', 'in', self.ids)])
            hydricmovements.mapped('presconsumption_id')
            hydricmovements.mapped('irrigationreport_id')
            for hydricmovement in hydricmovements:
                hydricmovement_ids.append(hydricmovement.id)
                if hydricmovement.presconsumption_id and \
                        hydricmovement.presconsumption_id.\
                        invoiced_consumption_quota:
                    quota_pres_consumption_ids.append(
                        hydricmovement.presconsumption_id.id)
                if hydricmovement.irrigationreport_id and \
                        hydricmovement.irrigationreport_id.\
                        invoiced_irrigationreport_quota:
                    quota_irrigationreport_ids.append(
                        hydricmovement.irrigationreport_id.id)
        res = super(WuaInvoiceset, self).unlink()
        allowed_multiple_invoicing_of_hydricmovement = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'allowed_multiple_invoicing_of_hydricmovement')
        if (allowed_multiple_invoicing_of_hydricmovement):
            self._update_hmovement_invoice_status(hydricmovement_ids)
        else:
            if hydricmovement_ids:
                hydricmovements = self.env['wua.hydricmovement'].browse(
                    hydricmovement_ids)
                vals = {
                    'invoiceset_id': None,
                    'invoiced_hydricmovement': False,
                    }
                hydricmovements.write(vals)
            if quota_pres_consumption_ids:
                quota_pres_consumption_ids = list(
                    set(quota_pres_consumption_ids))
                quota_pres_consumptions = self.env['wua.presconsumption'].\
                    browse(quota_pres_consumption_ids)
                quota_pres_consumptions.write(
                    {'invoiced_consumption_quota': False})
            if quota_irrigationreport_ids:
                quota_irrigationreport_ids = list(
                    set(quota_irrigationreport_ids))
                quota_irrigationreports = self.env['wua.irrigationreport'].\
                    browse(quota_irrigationreport_ids)
                quota_irrigationreports.write(
                    {'invoiced_irrigationreport_quota': False})
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 14:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        hydricmovement_ids = []
        for hydricmovement in \
            invoiceset_line.line_hydricmovement_ids.filtered(
                lambda x: x.selected is True):
            hydricmovement_ids.append(
                hydricmovement.hydricmovement_id.id)
        return hydricmovement_ids

    def get_hydricmovement_description(self, hydricmovement):
        description = ""
        if hydricmovement:
            event_time = self.env['wua.parcel'].transform_datetime_to_locale(
                hydricmovement.event_time)
            event_date = event_time[:10]
            language = hydricmovement.partner_id.lang
            hydricmovement_description = hydricmovement.description
            superproduct = hydricmovement.with_context(
                {'lang': language}).superproduct_id.name
            description = event_date + ', ' + superproduct + ', ' + \
                hydricmovement_description
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 14:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ14 = []
        invoicing_of_negative_hydricmovements_as_negative_values = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'invoicing_of_negative_hydricmovements_as_negative_values')
        hydricmovements = self.env['wua.hydricmovement'].browse(item_ids)
        for hydricmovement in hydricmovements:
            partner_id = hydricmovement.partner_id.id
            product_id = product_id
            categ_code = categ_code
            # Modified by EIS, 2022-12-29 (it is necessary for the separate
            # billing of the water connections applied to the water movements
            # mapped to the pressure consumption).
            # key1 = hydricmovement.id
            # if hydricmovement.type == 'pres_consumption':
            #     key2 = hydricmovement.presconsumption_id.id
            # else:
            #     key2 = 0
            key1 = 0
            key2 = 0
            if hydricmovement.type == 'pres_consumption':
                key2 = hydricmovement.presconsumption_id.id
                key1 = hydricmovement.presconsumption_id.waterconnection_id.id
            quantity = hydricmovement.volume
            # Check if quantity should be negative
            if ((hydricmovement.type == 'granted_cession' or
               hydricmovement.type == 'neg_indiv_assign') and
               invoicing_of_negative_hydricmovements_as_negative_values):
                quantity = -quantity
            description = self.get_hydricmovement_description(hydricmovement)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': key1,
                'key2': key2,
                'hydricmovement_id': hydricmovement.id,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ14.append(result)
        return invoice_details_categ14

    # If invoicing based on wc, fertconsumption on same griup as
    # presconsumption
    def get_invoice_details_to_group(self, invoice_details):
        invoice_details_to_group = super(WuaInvoiceset, self).\
            get_invoice_details_to_group(invoice_details)
        grouped_hydricmovements = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'invoicing_hydricmovement_grouped_by_wc')
        # Hydricmovement ONLY related to presconsumption: filter by type
        # without N+1 (browse all hydricmovement ids once).
        details_categ14 = [x for x in invoice_details if x['categ_code'] == 14]
        invoice_details_categ14 = []
        if details_categ14:
            hm_ids = list(set(x['hydricmovement_id'] for x in details_categ14))
            hydricmovements = self.env['wua.hydricmovement'].browse(hm_ids)
            pres_consumption_ids = set(
                hm.id for hm in hydricmovements if hm.type == 'pres_consumption')
            invoice_details_categ14 = [
                x for x in details_categ14
                if x['hydricmovement_id'] in pres_consumption_ids]
        if (grouped_hydricmovements and invoice_details_categ14):
            invoice_details_to_group = invoice_details_to_group + \
                invoice_details_categ14
        return invoice_details_to_group

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data, parcels_by_id=None):
        if categ_code != 14:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data,
                             parcels_by_id=parcels_by_id)
        data['waterconnection_id'] = invoice_data_line['key1']
        data['presconsumption_id'] = invoice_data_line['key2']
        data['hydricmovement_id'] = invoice_data_line['hydricmovement_id']
        return data

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        hydricmovement_ids = []
        quota_pres_consumption_ids = []
        quota_irrigationreport_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 14:
                for line_hydricmovement in line.line_hydricmovement_ids:
                    hydricmovement_ids.append(
                        line_hydricmovement.hydricmovement_id.id)
                    if line_hydricmovement.hydricmovement_id.\
                            presconsumption_id.invoiced_consumption_quota:
                        quota_pres_consumption_ids.append(
                            line_hydricmovement.hydricmovement_id.
                            presconsumption_id.id)
                    if line_hydricmovement.hydricmovement_id.\
                            irrigationreport_id.\
                            invoiced_irrigationreport_quota:
                        quota_irrigationreport_ids.append(
                            line_hydricmovement.hydricmovement_id.
                            irrigationreport_id.id)
        allowed_multiple_invoicing_of_hydricmovement = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'allowed_multiple_invoicing_of_hydricmovement')
        if (allowed_multiple_invoicing_of_hydricmovement):
            self._update_hmovement_invoice_status(hydricmovement_ids)
        else:
            if hydricmovement_ids:
                hydricmovement_ids = list(set(hydricmovement_ids))
                hydricmovements = \
                    self.env['wua.hydricmovement'].browse(hydricmovement_ids)
                hydricmovements.write({
                    'invoiced_hydricmovement': False,
                    'invoiceset_id': None,
                })
            if quota_pres_consumption_ids:
                quota_pres_consumption_ids = list(
                    set(quota_pres_consumption_ids))
                quota_pres_consumption = self.env['wua.presconsumption'].\
                    browse(quota_pres_consumption_ids)
                quota_pres_consumption.write(
                    {'invoiced_consumption_quota': False})
            if quota_irrigationreport_ids:
                quota_irrigationreport_ids = list(
                    set(quota_irrigationreport_ids))
                quota_irrigationreport = self.env['wua.irrigationreport'].\
                    browse(quota_irrigationreport_ids)
                quota_irrigationreport.write(
                    {'invoiced_irrigationreport_quota': False})

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 14:
                selected_hydricmovements = \
                    line.line_hydricmovement_ids.filtered(
                        lambda x: x.selected is True)
                quota_pres_consumption_ids = []
                quota_irrigationreport_ids = []
                for hidmov in selected_hydricmovements:
                    if hidmov.hydricmovement_id.presconsumption_id and \
                            hidmov.hydricmovement_id.type == \
                            'pres_consumption':
                        quota_pres_consumption_ids.append(
                            hidmov.hydricmovement_id.presconsumption_id.id)
                    if hidmov.hydricmovement_id.irrigationreport_id and \
                            hidmov.hydricmovement_id.type == \
                            'irrig_report':
                        quota_irrigationreport_ids.append(
                            hidmov.hydricmovement_id.irrigationreport_id.id)
                quota_pres_consumption = \
                    self.env['wua.presconsumption'].browse(
                        quota_pres_consumption_ids)
                quota_pres_consumption.write(
                    {'invoiced_consumption_quota': True})
                quota_irrigationreport = \
                    self.env['wua.irrigationreport'].browse(
                        quota_irrigationreport_ids)
                quota_irrigationreport.write(
                    {'invoiced_irrigationreport_quota': True})
                # Add invoiced and invoiceset_id to hydricmovement selected
                hydricmovement_ids = selected_hydricmovements.mapped(
                    lambda x: x.hydricmovement_id.id)
                if hydricmovement_ids:
                    hydricmovements = \
                        self.env['wua.hydricmovement'].browse(
                            hydricmovement_ids)
                    hydricmovements.write({
                        'invoiced_hydricmovement': True,
                        'invoiceset_id': invoiceset.id,
                        })
                # Removed lines not selected
                unselected_hydricmovements = \
                    line.line_hydricmovement_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_hydricmovements:
                    unselected_hydricmovements.unlink()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement', 'Hydricmovement')])

    line_hydricmovement_ids = fields.One2many(
        string="Selected items for invoice-set line",
        comodel_name="wua.invoiceset.line.hydricmovement",
        inverse_name="invoicesetline_id")

    def populate_items_select(self):
        if self.linkable_unit_type == 'hydricmovement':
            self.populate_items_select_hydricmovement()
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_hydricmovement(self):
        hydricmovements = self.env['wua.hydricmovement'].search(
            [('of_active_agriculturalseason', '=', True)])
        if hydricmovements:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            superproduct_id = self.product_id.related_product.\
                superproduct_id.id
            allowed_multiple_invoicing_of_hydricmovement = \
                self.env['ir.values'].get_default(
                    'wua.invoicing.configuration',
                    'allowed_multiple_invoicing_of_hydricmovement')
            invoicing_hydricmovement_selected_default = \
                self.env['ir.values'].get_default(
                    'wua.invoicing.configuration',
                    'invoicing_hydricmovement_selected_default')
            try:
                self.env.cr.savepoint()
                if allowed_multiple_invoicing_of_hydricmovement:
                    self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_hydricmovement (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, hydricmovement_id, selected,
                    quotaperiod_id, superproduct_id, partner_id, category_id,
                    event_time, volume, description, type)
                    SELECT
                    nextval('wua_invoiceset_line_hydricmovement_id_seq'),
                    %s, %s, now(), now(), %s, id, %s,
                    quotaperiod_id, superproduct_id, partner_id, category_id,
                    event_time, volume, description, type
                    FROM wua_hydricmovement WHERE of_active_agriculturalseason
                    AND superproduct_id = %s
                    AND CASE
                            WHEN type = 'grav_consumption'
                            THEN gravconsumption_id
                                IN (SELECT id FROM wua_gravconsumption WHERE
                                    state = 'executed')
                            ELSE TRUE
                        END;
                    """, (user_id, user_id, invoicesetline_id,
                          "TRUE" if invoicing_hydricmovement_selected_default
                          else "FALSE",
                          superproduct_id,
                          ))
                else:
                    self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_hydricmovement (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, hydricmovement_id, selected,
                    quotaperiod_id, superproduct_id, partner_id, category_id,
                    event_time, volume, description, type)
                    SELECT
                    nextval('wua_invoiceset_line_hydricmovement_id_seq'),
                    %s, %s, now(), now(), %s, id, %s,
                    quotaperiod_id, superproduct_id, partner_id, category_id,
                    event_time, volume, description, type
                    FROM wua_hydricmovement WHERE of_active_agriculturalseason
                    AND superproduct_id = %s AND NOT COALESCE(
                        invoiced_hydricmovement, FALSE)
                    AND CASE
                            WHEN type = 'grav_consumption'
                            THEN gravconsumption_id
                                IN (SELECT id FROM wua_gravconsumption WHERE
                                    state = 'executed')
                            ELSE TRUE
                        END;
                    """, (user_id, user_id, invoicesetline_id,
                          "TRUE" if invoicing_hydricmovement_selected_default
                          else "FALSE",
                          superproduct_id,
                          ))
                self.env.cr.commit()
                self.env.invalidate_all()
                # self.env.cr.execute("""
                #     UPDATE wua_hydricmovement
                #     SET invoiceset_id=""" + str(self.invoiceset_id.id) +
                #                     """,
                #     invoiced_hydricmovement=TRUE
                #     WHERE
                #     of_active_agriculturalseason AND NOT
                #     invoiced_hydricmovement""")
                # self.env.cr.commit()
                # self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))
            # The "number_of_invoices" field is a non-persistent field in
            # the wua.hydricmovement model, so that field cannot be in the
            # SQL statement and needs to be processed.
            for line in (self.line_hydricmovement_ids or []):
                line.number_of_invoices = \
                    line.hydricmovement_id.number_of_invoices

    @api.depends('line_hydricmovement_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'hydricmovement':
                record.configured_line = \
                    len(record.line_hydricmovement_ids) > 0

    @api.multi
    def unlink(self):
        for record in self:
            hydricmovement_ids = []
            for line_hydricmovement in record.line_hydricmovement_ids:
                hydricmovement_ids.append(
                    line_hydricmovement.hydricmovement_id.id)
            allowed_multiple_invoicing_of_hydricmovement = \
                self.env['ir.values'].get_default(
                    'wua.invoicing.configuration',
                    'allowed_multiple_invoicing_of_hydricmovement')
            if (allowed_multiple_invoicing_of_hydricmovement):
                self.env['wua.invoiceset']._update_hmovement_invoice_status(
                    hydricmovement_ids)
            else:
                if hydricmovement_ids:
                    hydricmovements = self.env['wua.hydricmovement'].browse(
                        hydricmovement_ids)
                    hydricmovements.write({
                        'invoiceset_id': None,
                        'invoiced_hydricmovement': False,
                    })
        return super(WuaInvoicesetLine, self).unlink()

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'hydricmovement':
            name = _('Hydricmovement')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.hydricmovement'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineHydricmovement(models.Model):
    _name = 'wua.invoiceset.line.hydricmovement'
    _description = 'Hydricmovement of an invoice-set line'
    _order = 'invoicesetline_id,hydricmovement_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    hydricmovement_id = fields.Many2one(
        string='Hydricmovement',
        comodel_name='wua.hydricmovement',
        required=True,
        ondelete='restrict')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        ondelete="restrict")

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        ondelete="restrict")

    event_time = fields.Datetime(
        string='Time',
        required=True,
        index=True,
        readonly=True)

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 2),
        default=0,
        required=True,
        readonly=True)

    description = fields.Char(
        string='Description',
        index=True,
    )

    type = fields.Selection([
        ('multiple_assign', 'Multiple Assignment'),
        ('pos_indiv_assign', 'Individual Assignment'),
        ('received_cession', 'Received Cession'),
        ('pres_consumption', 'Pressurized Consumption'),
        ('grav_consumption', 'Gravity Consumption'),
        ('irrig_report', 'Irrigation Report'),
        ('neg_indiv_assign', 'Negative Individual Assignment'),
        ('granted_cession', 'Granted Cession'),
        ('input_prev_quota', 'Input from previous quota'),
        ('output_next_quota', 'Output to next quota')],
        string='Type',
        required=True,
        readonly=True,
    )

    number_of_invoices = fields.Integer(
        string='Billings',
        default=0)

    @api.multi
    def add_to_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': True,
                }
            self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': False,
                }
            self.write(vals)
