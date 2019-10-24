# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('enrolledsubparcel', 'Enrolled Subparcels')])


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

    #@TODO
    subparcel_code = fields.Many2one(
        string='Subparcel Code',
        comodel_name='wua.enrolledsubparcel',
        store=True,
        index=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        ondelete='set null',
        readonly=True)

    subparceltype_id = fields.Many2one(
        string='Type',
        comodel_name='wua.subparceltype',
        required=True,
        index=True,
        ondelete='restrict')

    #@TODO
#     area_official = fields.Float(
#         string='Area',
#         digits=(32, 4),
#         store=True,
#         compute='_compute_area_official')

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        index=True,
        ondelete='restrict')

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        index=True,
        ondelete='restrict')

    profile = fields.Many2one(
        string='Profile',
        comodel_name='wua.enrolledsubparcel',
        index=True,
        ondelete='restrict')

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
        index=True,
        ondelete='restrict')

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        index=True,
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    @api.depends('enrolledsubparcel_id')
    def _compute_subparcel_code(self):
        for record in self:
            record.subparcel_code = record.subparcel_code

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