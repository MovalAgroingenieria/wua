# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 21:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        partner_concession_as_volume_ids = []
        for partner_concession_as_volume in \
            invoiceset_line.line_partner_concession_ids.filtered(
                lambda x: x.selected is True):
            partner_concession_as_volume_ids.append(
                partner_concession_as_volume.partner_id.id)
        return partner_concession_as_volume_ids

    def get_partner_concession_as_volume_description(
            self, partner_id):
        description = ''
        partner_id = self.env['res.partner'].browse(partner_id)
        lang = partner_id.lang or 'es_ES'
        concession_as_volume = partner_id.concession_as_volume
        default_partner_label = _('Partner:')
        partner_label = \
            self.get_value_from_translation(
                'base_wua_invoicing_partner_concession_as_volume',
                'Partner:',
                lang)
        if not partner_label:
            partner_label = default_partner_label
        default_concession_label = _('Concession:')
        concessison_label = \
            self.get_value_from_translation(
                'base_wua_invoicing_partner_concession_as_volume',
                'Concession:',
                lang)
        if not concessison_label:
            concessison_label = default_concession_label
        if partner_id and concession_as_volume:
            partner_name = partner_id.name
            description = partner_label + u' ' + \
                partner_name + u' ' + concessison_label + u' ' + \
                str(concession_as_volume) + u' m³'
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 21:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ21 = []
        description = ''
        product = self.env['product.product'].browse(product_id)
        if product:
            partner_ids = self.env['res.partner'].browse(item_ids)
        for partner in partner_ids:
            quantity = partner.concession_as_volume
            description = self.get_partner_concession_as_volume_description(
                partner.id)
            result = {
                'partner_id': partner.id,
                'product_id': product.id,
                'categ_code': categ_code,
                'key1': partner,
                'key2': None,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ21.append(result)
        return invoice_details_categ21


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('partner_concession', _('Partner concession as volume'))])

    line_partner_concession_ids = fields.One2many(
        string='Selected items for invoice-set line',
        comodel_name='wua.invoiceset.line.partner.concession',
        inverse_name='invoicesetline_id')

    def populate_items_select(self):
        if self.linkable_unit_type == 'partner_concession':
            self.populate_items_select_partner_concession()
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_partner_concession(self):
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)])
        if len(partners) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_partner_concession (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, partner_id, is_company,
                    is_owner, is_lessee, is_payer, parcel_owner_number,
                    parcel_owner_area,
                    parcel_lessee_number, parcel_lessee_area,
                    parcel_payer_number, parcel_payer_area, number_of_votes,
                    concession_as_volume)
                    SELECT
                    nextval('wua_invoiceset_line_partner_concession_id_seq'),
                    %s,
                    %s, now(), now(), %s, TRUE, id, is_company, is_owner,
                    is_lessee, is_payer, parcel_owner_number,
                    parcel_owner_area, parcel_lessee_number,
                    parcel_lessee_area, parcel_payer_number,
                    parcel_payer_area, number_of_votes, concession_as_volume
                    FROM res_partner WHERE active=TRUE and
                    is_wua_partner=TRUE and concession_as_volume > 0 and
                    partner_type != '01_WUA'
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    @api.depends('line_partner_concession_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'partner_concession':
                record.configured_line = \
                    len(record.line_partner_concession_ids) > 0

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
        if self.linkable_unit_type == 'partner_concession':
            name = _('Partner concessions')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.partner.concession'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLinePartnerConcession(models.Model):
    _name = 'wua.invoiceset.line.partner.concession'
    _description = 'Partner concessions of a invoice-set line'
    _order = 'invoicesetline_id,partner_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    partner_id = fields.Many2one(
        string='Name',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict')

    concession_as_volume = fields.Float(
        string='Concession as Volume',
        default=0
    )

    is_company = fields.Boolean(
        string='Is a Company', default=False)

    is_owner = fields.Boolean(
        string="Is Owner", default=False)

    is_lessee = fields.Boolean(
        string="Is Lessee", default=False)

    is_payer = fields.Boolean(
        string="Is Payer", default=False)

    parcel_owner_number = fields.Integer(
        string="Parcels, as owner",
        default=0)

    parcel_owner_area = fields.Float(
        string="Area, as owner",
        digits=(32, 4),
        default=0)

    parcel_lessee_number = fields.Integer(
        string="Parcels, as lessee",
        default=0)

    parcel_lessee_area = fields.Float(
        string="Area, as lessee",
        digits=(32, 4),
        default=0)

    parcel_payer_number = fields.Integer(
        string="Parcels, as payer",
        default=0)

    parcel_payer_area = fields.Float(
        string="Area, as payer",
        digits=(32, 4),
        default=0)

    number_of_votes = fields.Integer(
        string="Number of votes", default=0)

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
