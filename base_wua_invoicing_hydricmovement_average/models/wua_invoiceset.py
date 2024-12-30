# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 20:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        hydricmovement_average_ids = []
        for hydricmovement_average in \
            invoiceset_line.line_hydricmovement_average_ids.filtered(
                lambda x: x.selected is True):
            hydricmovement_average_ids.append(
                hydricmovement_average.id)
        return hydricmovement_average_ids

    def get_hydricmovement_average_description(
            self, partner_id, type, superproduct_id, agriculturalseasons):
        description = ''
        partner_id = self.env['res.partner'].browse(partner_id)
        lang = partner_id.lang or 'es_ES'
        superproduct = self.env['wua.superproduct'].browse(superproduct_id)
        parcel_model = self.env['wua.parcel'].with_context({'lang': lang})
        default_average_label = _('Average of')
        average_label = \
            self.get_value_from_translation(
                'base_wua_invoicing_hydricmovement_average',
                'Average of',
                lang)
        if not average_label:
            average_label = default_average_label
        default_of_label = _('of')
        of_label = \
            self.get_value_from_translation(
                'base_wua_invoicing_hydricmovement_average',
                'of',
                lang)
        if not of_label:
            of_label = default_of_label
        hmov_model = self.env[
            'wua.hydricmovement'].sudo()
        if type and superproduct and agriculturalseasons:
            agseasons = self.env['wua.agriculturalseason'].search(
                [('id', 'in', list(agriculturalseasons.keys()))],
                order='initial_date asc')
            type_name = hmov_model._fields['type'].\
                convert_to_export(type, self)
            agseasons_values = []
            for agseason in agseasons:
                agseason_values = agseason.description
                agseason_values += u': ' + \
                    parcel_model.transform_float_to_locale(
                        agriculturalseasons[agseason.id], 2) + u' m³'
                agseasons_values.append(agseason_values)
            description = average_label + u' ' + \
                type_name + u' ' + of_label + u' ' + superproduct.with_context(
                    {'lang': lang}).name + \
                u' (' + ', '.join(agseasons_values) + u')'
        return description

    def get_average_of_hmovements(self, hydricmovement_averages):
        grouped_hydricmovement_averages = defaultdict(
            lambda: {'agseason_volumes': defaultdict(float)},
        )
        for hydricmovement_average in hydricmovement_averages:
            key = (
                hydricmovement_average.partner_id.id,
                hydricmovement_average.type,
                hydricmovement_average.superproduct_id.id,
            )
            agseason_id = hydricmovement_average['agriculturalseason_id'].id
            volume = hydricmovement_average['volume']
            grouped_hydricmovement_averages[key]['agseason_volumes'][
                agseason_id] += volume
        return grouped_hydricmovement_averages

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 20:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ20 = []
        invoicing_of_negative_hydricmovements_as_negative_values = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'invoicing_of_negative_hydricmovements_as_negative_values')
        hydricmovement_averages = self.env[
            'wua.invoiceset.line.hydricmovement.average'].browse(item_ids)
        for (partner_id, type, superproduct_id), hydricmovement_average in \
                self.get_average_of_hmovements(
                    hydricmovement_averages).items():
            agriculturalseasons = hydricmovement_average[
                'agseason_volumes']
            agriculturalseason_count = len(agriculturalseasons)
            product_id = product_id
            quantity = sum(agriculturalseasons.values()) / \
                agriculturalseason_count if agriculturalseason_count > 0 else 0
            # Check if quantity should be negative
            if ((type in ['granted_cession', 'neg_indiv_assign']) and
               invoicing_of_negative_hydricmovements_as_negative_values):
                quantity = -quantity
            description = self.get_hydricmovement_average_description(
                partner_id, type, superproduct_id, agriculturalseasons)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': partner_id,
                'key2': None,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ20.append(result)
        return invoice_details_categ20


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement_average', 'Hydricmovement Average')])

    line_hydricmovement_average_ids = fields.One2many(
        string='Selected items for invoice-set line',
        comodel_name='wua.invoiceset.line.hydricmovement.average',
        inverse_name='invoicesetline_id')

    def populate_items_select(self):
        if self.linkable_unit_type == 'hydricmovement_average':
            self.populate_items_select_hydricmovement_average()
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_hydricmovement_average(self):
        hydricmovements = self.env['wua.hydricmovement'].search(
            [], limit=1)
        if hydricmovements:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            invoicing_hydricmovement_selected_default = \
                self.env['ir.values'].get_default(
                    'wua.invoicing.configuration',
                    'invoicing_hydricmovement_selected_default')
            select_cancelled = self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'invoicing_of_hydricmovements_cancelled')
            where_clause = ""
            if not select_cancelled:
                where_clause = "WHERE related_element_cancelled = FALSE"
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    """
                    INSERT INTO wua_invoiceset_line_hydricmovement_average
                        (id, create_uid, write_uid, create_date, write_date,
                        invoicesetline_id, selected, agriculturalseason_id,
                        superproduct_id,
                        partner_id, volume, type)
                    SELECT
                        nextval('wua_invoiceset_line_hydricmovement_id_seq'),
                        %s, %s, now(), now(), %s, %s,
                        agriculturalseason_id, superproduct_id,
                        partner_id, SUM(volume), type
                    FROM
                        wua_hydricmovement
                    GROUP BY
                        partner_id, agriculturalseason_id, type,
                        superproduct_id
                    """ + where_clause,
                    (user_id, user_id, invoicesetline_id,
                     "TRUE" if invoicing_hydricmovement_selected_default
                     else "FALSE"))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))

    @api.depends('line_hydricmovement_average_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'hydricmovement_average':
                record.configured_line = \
                    len(record.line_hydricmovement_average_ids) > 0

    @api.multi
    def action_select_linked_items(self):
        self.ensure_one()
        if not self.configured_line:
            self.populate_items_select()
        data_items_select = self.get_data_items_select(self.product_id.name)
        if data_items_select:
            if ('name' in data_items_select and
               'res_model' in data_items_select):
                if (data_items_select['name'] != '' and
                   data_items_select['res_model'] != ''):
                    act_window = {
                        'type': 'ir.actions.act_window',
                        'name': data_items_select['name'],
                        'res_model': data_items_select['res_model'],
                        'view_type': 'form',
                        'view_mode': 'tree',
                        'domain': [['invoicesetline_id', '=', self.id]],
                        'limit': 10000000,
                        }
                    return act_window

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'hydricmovement_average':
            name = _('Hydricmovement Average')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.hydricmovement.average'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineHydricmovementAverage(models.Model):
    _name = 'wua.invoiceset.line.hydricmovement.average'
    _description = 'Hydricmovement Avergae of an invoice-set line'
    _order = 'invoicesetline_id,agriculturalseason_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade',
        index=True,
    )

    selected = fields.Boolean(
        string='Selected',
        default=True,
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='restrict',
    )

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        ondelete='restrict',
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        ondelete='restrict',
    )

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 2),
        default=0,
        required=True,
        readonly=True,
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

    @api.multi
    def add_to_invoiceset(self):
        vals = {'selected': True}
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {'selected': False}
        self.write(vals)
