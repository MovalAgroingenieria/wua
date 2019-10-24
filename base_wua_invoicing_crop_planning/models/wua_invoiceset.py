# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


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
