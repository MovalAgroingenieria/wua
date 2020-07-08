# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    # Fields
    entity_type_code = fields.Selection([
        ('A', 'Town hall'),
        ('C', 'Water user assotiation')],
        string="Entity type",
        help="The type of entity",
        default="C",
        compute="get_entity_type_code",
        readonly=True)

    # Hooks (wua implemented)
    def get_entity_type_code(self):
        # Entity type code
        # Positions [015-015] Length 1
        # @INFO: It is always C, that identify wua in spanish
        self.entity_type_code = 'C'
        entity_type_code = self.entity_type_code
        return entity_type_code

    def get_fixed_number(self, partner_id):
        # Fixed number
        # Position [223-234] Length 12
        # @INFO: Is the wua associate number
        #        The format depends on each wua
        if partner_id.partner_code:
            # Format 5 numbers padded with zeros 
            # and padded to 12 with white spaces
            fixed_number = str(partner_id.partner_code).zfill(5).ljust(12)
        else:
            raise ValidationError(
                _("Fail, partner code not found for partner %s." %
                  (partner_id.name)))
        return fixed_number

    @api.multi
    def generated2uploaded(self):
        res = super(AccountPaymentOrder, self).generated2uploaded()
        for order in self:
            if order.payment_mode_id.name == 'SUMA':
                for bline in order.bank_line_ids:
                    if bline.suma_sent:
                        invoice = self.env['account.invoice'].search([
                            ('number', '=', bline.communication)])
                        move_lines = self.env['account.move.line'].search([
                            ('invoice_id', '=', invoice.id)])
                        if move_lines:
                            for move_line in move_lines:
                                move_line.suma_ref = bline.suma_ref
                        invoice.write({
                            'in_suma': True,
                            'suma_ref': bline.suma_ref,
                        })
        return res
