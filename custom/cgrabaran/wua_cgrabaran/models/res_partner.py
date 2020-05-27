# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from math import ceil, floor
from lxml import etree
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    number_of_votes_company_01 = fields.Integer(
        string="Number of votes",
        store=True,
        compute='_compute_number_of_votes_company_01')

    number_of_votes_company_02 = fields.Integer(
        string="Number of votes",
        store=True,
        compute='_compute_number_of_votes_company_02')

    number_of_votes_company_03 = fields.Integer(
        string="Number of votes",
        store=True,
        compute='_compute_number_of_votes_company_03')

    parcel_owner_number_company_01 = fields.Integer(
        string="Parcels of company_01, as owner",
        default=0)

    parcel_owner_number_company_02 = fields.Integer(
        string="Parcels of company_02, as owner",
        default=0)

    parcel_owner_number_company_03 = fields.Integer(
        string="Parcels of company_03, as owner",
        default=0)

    parcel_owner_area_hec_company_01 = fields.Float(
        string="Area, as owner company_01 (hectares)",
        digits=(32, 4))

    parcel_owner_area_hec_company_02 = fields.Float(
        string="Area, as owner company_02 (hectares)",
        digits=(32, 4))

    parcel_owner_area_hec_company_03 = fields.Float(
        string="Area, as owner company_03 (hectares)",
        digits=(32, 4))

    area_total_company_g = fields.Float(
        string='Area of Grupo (ha)',
        digits=(32, 4),
        compute="_compute_area_total_company_g")

    area_total_company_r = fields.Float(
        string='Area of Resurrección (ha)',
        digits=(32, 4),
        compute="_compute_area_total_company_r")

    area_total_company_t = fields.Float(
        string='Area of Trasvase (ha)',
        digits=(32, 4),
        compute="_compute_area_total_company_t")

    @api.depends('parcel_owner_number_company_01',
                 'parcel_owner_area_hec_company_01')
    def _compute_number_of_votes_company_01(self):
        if len(self) != 1:
            return
        votes = 0
        if self.parcel_owner_number_company_01 > 0 or \
                self.parcel_owner_area_hec_company_01 > 0:
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type_company_01')
            company_01 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_01')
            if polling_system_type > 0 and company_01:
                if polling_system_type == 1:
                    votes = self.parcel_owner_number_company_01
                if polling_system_type == 2 or polling_system_type == 3:
                    area_for_votes = self.parcel_owner_area_hec_company_01 \
                        * 10000
                    if polling_system_type == 2:
                        polling_system_interval = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_interval_company_01')
                        if polling_system_interval > 0:
                            polling_system_rounding_type = \
                                self.env['ir.values'].\
                                get_default(
                                    'wua.configuration',
                                    'polling_system_rounding_type_company_01')
                            calc_votes =\
                                area_for_votes / polling_system_interval
                            if polling_system_rounding_type == 0:
                                votes = ceil(calc_votes)
                            else:
                                votes = floor(calc_votes)
                    if polling_system_type == 3:
                        polling_system_intervals = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_intervals_company_01')
                        if polling_system_intervals:
                            votes = self.assign_votes_by_range(
                                area_for_votes, polling_system_intervals)
        self.number_of_votes_company_01 = votes

    @api.depends('parcel_owner_number_company_02',
                 'parcel_owner_area_hec_company_02')
    def _compute_number_of_votes_company_02(self):
        if len(self) != 1:
            return
        votes = 0
        if self.parcel_owner_number_company_02 > 0 or \
                self.parcel_owner_area_hec_company_02 > 0:
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type_company_02')
            company_02 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_02')
            if polling_system_type > 0 and company_02:
                if polling_system_type == 1:
                    votes = self.parcel_owner_number_company_02
                if polling_system_type == 2 or polling_system_type == 3:
                    area_for_votes = self.parcel_owner_area_hec_company_02 \
                        * 10000
                    if polling_system_type == 2:
                        polling_system_interval = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_interval_company_02')
                        if polling_system_interval > 0:
                            polling_system_rounding_type = \
                                self.env['ir.values'].\
                                get_default(
                                    'wua.configuration',
                                    'polling_system_rounding_type_company_02')
                            calc_votes =\
                                area_for_votes / polling_system_interval
                            if polling_system_rounding_type == 0:
                                votes = ceil(calc_votes)
                            else:
                                votes = floor(calc_votes)
                    if polling_system_type == 3:
                        polling_system_intervals = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_intervals_company_02')
                        if polling_system_intervals:
                            votes = self.assign_votes_by_range(
                                area_for_votes, polling_system_intervals)
        self.number_of_votes_company_02 = votes

    @api.depends('parcel_owner_number_company_03',
                 'parcel_owner_area_hec_company_03')
    def _compute_number_of_votes_company_03(self):
        if len(self) != 1:
            return
        votes = 0
        if self.parcel_owner_number_company_03 > 0 or \
                self.parcel_owner_area_hec_company_03 > 0:
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type_company_03')
            company_03 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_03')
            if polling_system_type > 0 and company_03:
                if polling_system_type == 1:
                    votes = self.parcel_owner_number_company_03
                if polling_system_type == 2 or polling_system_type == 3:
                    area_for_votes = self.parcel_owner_area_hec_company_03 \
                        * 10000
                    if polling_system_type == 2:
                        polling_system_interval = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_interval_company_03')
                        if polling_system_interval > 0:
                            polling_system_rounding_type = \
                                self.env['ir.values'].\
                                get_default(
                                    'wua.configuration',
                                    'polling_system_rounding_type_company_03')
                            calc_votes =\
                                area_for_votes / polling_system_interval
                            if polling_system_rounding_type == 0:
                                votes = ceil(calc_votes)
                            else:
                                votes = floor(calc_votes)
                    if polling_system_type == 3:
                        polling_system_intervals = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_intervals_company_03')
                        if polling_system_intervals:
                            votes = self.assign_votes_by_range(
                                area_for_votes, polling_system_intervals)
        self.number_of_votes_company_03 = votes

    @api.multi
    def _compute_area_total_company_g(self):
        company_01_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_01')
        for record in self:
            links_company_01 = record.env['wua.parcel.partnerlink'].search([
                ('partner_id', '=', record.id),
                ('company_id', '=', company_01_id)])
            area_total_company_g = 0.0
            if links_company_01:
                for link in links_company_01:
                    area_total_company_g += link.area_official_water_costs_net
            record.area_total_company_g = area_total_company_g

    @api.multi
    def _compute_area_total_company_r(self):
        company_02_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_02')
        for record in self:
            links_company_02 = record.env['wua.parcel.partnerlink'].search([
                ('partner_id', '=', record.id),
                ('company_id', '=', company_02_id)])
            area_total_company_r = 0.0
            if links_company_02:
                for link in links_company_02:
                    area_total_company_r += link.area_official_water_costs_net
            record.area_total_company_r = area_total_company_r

    @api.multi
    def _compute_area_total_company_t(self):
        company_03_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_03')
        for record in self:
            links_company_03 = record.env['wua.parcel.partnerlink'].search([
                ('partner_id', '=', record.id),
                ('company_id', '=', company_03_id)])
            area_total_company_t = 0.0
            if links_company_03:
                for link in links_company_03:
                    area_total_company_t += link.area_official_water_costs_net
            record.area_total_company_t = area_total_company_t

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id,
                                                      view_type=view_type,
                                                      toolbar=toolbar,
                                                      submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            company_01_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_01_abv')
            company_02_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_02_abv')
            company_03_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_03_abv')
            votes_of_string = _('Votes of')
            if company_01_abv:
                for node in doc.xpath(
                        "//field[@name='number_of_votes_company_01']"):
                    node.set('string',
                             votes_of_string + ' ' +
                             company_01_abv.decode('utf-8'))
            if company_02_abv:
                for node in doc.xpath(
                        "//field[@name='number_of_votes_company_02']"):
                    node.set('string',
                             votes_of_string + ' ' +
                             company_02_abv.decode('utf-8'))
            if company_03_abv:
                for node in doc.xpath(
                        "//field[@name='number_of_votes_company_03']"):
                    node.set('string',
                             votes_of_string + ' ' +
                             company_03_abv.decode('utf-8'))
            res['arch'] = etree.tostring(doc)
        return res
