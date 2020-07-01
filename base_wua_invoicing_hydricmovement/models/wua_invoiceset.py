# -*- coding: utf-8 -*-
# Cpyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to make the hydricmovement
    # selectable again by setting it as not invoiced and remove the invoceset
    # associated
    @api.multi
    def unlink(self):
        hydricmovement_ids = []
        for record in self:
            for line in record.line_ids:
                if line.categ_id.productcategory_code == 14:
                    for l_hydricmovement in line.line_hydricmovement_ids:
                        hydricmovement_ids.append(
                            l_hydricmovement.hydricmovement_id.id)
        res = super(WuaInvoiceset, self).unlink()
        if hydricmovement_ids:
            hydricmovement_ids = list(set(hydricmovement_ids))
            hydricmovements = \
                self.env['wua.hydricmovement'].browse(hydricmovement_ids)
            hydricmovements.write({
                'invoiced_hydricmovement': False,
                'invoiceset_id': None
            })
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
            event_time = datetime.datetime.strptime(
                hydricmovement.event_time, '%Y-%m-%d %H:%M:%S')
            event_time = event_time.strftime('%x')
            language = hydricmovement.partner_id.lang
            hydricmovement_description = hydricmovement.description
            superproduct = hydricmovement.with_context(
                {'lang': language}).superproduct_id.name
            description = event_time + ', ' + superproduct + ', ' + \
                hydricmovement_description
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 14:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ14 = []
        hydricmovements = self.env['wua.hydricmovement'].browse(item_ids)
        for hydricmovement in hydricmovements:
            partner_id = hydricmovement.partner_id.id
            product_id = product_id
            categ_code = categ_code
            quantity = hydricmovement.volume
            description = self.get_hydricmovement_description(hydricmovement)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': 0,
                'key2': 0,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ14.append(result)
        return invoice_details_categ14

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        hydricmovement_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 14:
                for line_hydricmovement in line.line_hydricmovement_ids:
                    hydricmovement_ids.append(
                        line_hydricmovement.hydricmovement_id.id)
        if hydricmovement_ids:
            hydricmovement_ids = list(set(hydricmovement_ids))
            hydricmovements = \
                self.env['wua.hydricmovement'].browse(hydricmovement_ids)
            hydricmovements.write({
                'invoiced_hydricmovement': False,
                'invoiceset_id': None
            })

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 14:
                unselected_hydricmovements = \
                    line.line_hydricmovement_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_hydricmovements:
                    hydricmovement_ids = []
                    for line_hydricmovement in unselected_hydricmovements:
                        hydricmovement_ids.append(
                            line_hydricmovement.hydricmovement_id.id)
                    if hydricmovement_ids:
                        hydricmovements = \
                            self.env['wua.hydricmovement'].browse(
                                hydricmovement_ids)
                        hydricmovements.write({
                            'invoiceset_id': None,
                            'invoiced_hydricmovement': False,
                            })
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
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                INSERT INTO wua_invoiceset_line_hydricmovement (id,
                create_uid,write_uid,create_date,write_date,invoicesetline_id,
                hydricmovement_id, selected, quotaperiod_id,superproduct_id,
                partner_id,event_time, volume, description, type)
                SELECT nextval('wua_invoiceset_line_hydricmovement_id_seq'),
                %s,%s,now(),now(),%s,wh1.id, TRUE,
                wh1.quotaperiod_id, wh1.superproduct_id, wh1.partner_id,
                wh1.event_time, wh1.volume, wh1.description, wh1.type
                FROM wua_hydricmovement wh1 INNER JOIN wua_agriculturalseason
                wa1 ON wh1.agriculturalseason_id = wa1.id WHERE
                wa1.active_agriculturalseason AND NOT
                wh1.invoiced_hydricmovement
                """,
                                    (user_id, user_id, invoicesetline_id))
                self.env.cr.execute("""
                    UPDATE wua_hydricmovement
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) +
                                    """,
                    invoiced_hydricmovement=TRUE
                    FROM wua_hydricmovement wh1 INNER JOIN
                    wua_agriculturalseason wa1 ON
                    wh1.agriculturalseason_id = wa1.id WHERE
                    wa1.active_agriculturalseason AND
                    wh1.invoiceset_id is null""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))

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
                if hydricmovement_ids:
                    hydricmovements = self.env['wua.hydricmovement'].browse(
                        hydricmovement_ids)
                    hydricmovements.write({
                        'invoiceset_id': None,
                        'invoiced_hydricmovement': False,
                    })
                    return super(WuaInvoicesetLine, self).unlink()

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
                        'domain': [["invoicesetline_id", "=", self.id]],
                        'limit': 10000000,
                        }
                    return act_window

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
        index=True,)

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
        readonly=True,)

    @api.multi
    def add_to_invoiceset(self):
        vals = {'selected': True, }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {'selected': False, }
        self.write(vals)
