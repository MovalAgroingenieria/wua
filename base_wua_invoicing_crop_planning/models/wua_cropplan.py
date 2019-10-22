# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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
                    invoiceset_ids.appends(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.depends('number_of_invoicing_processes')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = record.number_of_invoicing_processes > 0
