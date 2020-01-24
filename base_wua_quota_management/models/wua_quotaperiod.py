# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaQuotaperiod(models.Model):
    _name = 'wua.quotaperiod'
    _description = 'Quota Period'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 40

    def _default_agriculturalseason_id(self):
        resp = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            resp = active_agriculturalseasons[0].id
        return resp

    def _default_sorted_quotas(self):
        default_sorted_quotas = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'sorted_quotas')
        return default_sorted_quotas

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
        index=True)

    end_date = fields.Date(
        string='End Date',
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    name = fields.Char(
        string='Quota Period',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    initialized_agriculturalseason = fields.Boolean(
        string="Initialized Agricultural Season",
        compute="_compute_initialized_agriculturalseason")

    number_of_superproducts = fields.Integer(
        string='Number of superproducts',
        store=True,
        compute='_compute_number_of_superproducts')

    sorted_quotas = fields.Boolean(
        string='Sort in superproducts',
        default=_default_sorted_quotas)

    volume_total = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume_total')

    is_closed = fields.Boolean(
        string='Closed Period',
        default=False,
        track_visibility='onchange')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('configured', 'Configured'),
            ('generated', 'Generated'),
        ],
        index=True,
        required=True,
        string='State',
        default='draft',
        track_visibility='onchange')

    quotaperiodline_ids = fields.One2many(
        string='Associated Superproducts',
        comodel_name='wua.quotaperiod.line',
        inverse_name='quotaperiod_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('agriculturalseason_id', 'initial_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.initial_date:
                name = record.initial_date
            record.name = name

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.multi
    def _compute_initialized_agriculturalseason(self):
        for record in self:
            initialized_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.initialized):
                initialized_agriculturalseason = True
            record.initialized_agriculturalseason = \
                initialized_agriculturalseason

    @api.depends('quotaperiodline_ids')
    def _compute_number_of_superproducts(self):
        for record in self:
            number_of_superproducts = 0
            if record.quotaperiodline_ids:
                number_of_superproducts = len(record.quotaperiodline_ids)
            record.number_of_superproducts = number_of_superproducts

    @api.depends('quotaperiodline_ids', 'quotaperiodline_ids.volume_total')
    def _compute_volume_total(self):
        for record in self:
            volume_total = 0
            if record.quotaperiodline_ids:
                volume_total = sum(x.volume_total
                                   for x in record.quotaperiodline_ids)
            record.volume_total = volume_total

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1 and
           ((self.initial_date < self.agriculturalseason_id.initial_date) or
           (self.end_date > self.agriculturalseason_id.end_date))):
            raise exceptions.ValidationError(_(
                'The quota period limits are outside the agricultural '
                'season.'))

    @api.model
    def create(self, vals):
        self._populate_pos_in_quotaperiodlines(vals)
        if not self._quotaperiodlines_no_repeat(vals):
            raise exceptions.UserError(_('There are repeated lines.'))
        return super(WuaQuotaperiod, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            self._populate_pos_in_quotaperiodlines(vals)
            if not self._quotaperiodlines_no_repeat(vals):
                raise exceptions.UserError(_('There are repeated lines.'))
        super(WuaQuotaperiod, self).write(vals)
        return True

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.end_date, '%Y-%m-%d').strftime('%x')
            name = initial_date_str + ' - ' + end_date_str
            description = ''
            if record.description:
                description = record.description.strip()
            if description:
                name = name + ' (' + description + ')'
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise exceptions.UserError(_(
                    'You can only delete a quota period if it is in '
                    'draft state.'))
        return super(WuaQuotaperiod, self).unlink()

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_partner_quotas'

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        # Provisional
        print 'action_get_hydric_movements'

    @api.multi
    def action_configure_quotaperiod(self):
        self.ensure_one()
        view_id = self.env.ref(
            'base_wua_quota_management.wua_config_quotaperiod_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Configuration of Quota-Period Lines'),
            'res_model': 'wua.quotaperiod',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'res_id': self.id,
            }
        return act_window

    def _populate_pos_in_quotaperiodlines(self, vals):
        if vals and 'quotaperiodline_ids' in vals:
            last_pos = 0
            max_quotaperiodline_id = 0
            for quotaperiodline in vals['quotaperiodline_ids']:
                quotaperiodline_oper = quotaperiodline[0]
                quotaperiodline_id = quotaperiodline[1]
                if quotaperiodline_oper == 1 or quotaperiodline_oper == 4:
                    if quotaperiodline_id > max_quotaperiodline_id:
                        max_quotaperiodline_id = quotaperiodline_id
            if max_quotaperiodline_id > 0:
                last_quotaperiodline = self.env['wua.quotaperiod.line'].browse(
                    max_quotaperiodline_id)
                if last_quotaperiodline:
                    last_pos = last_quotaperiodline.pos
            pos = last_pos + 1
            for quotaperiodline in vals['quotaperiodline_ids']:
                quotaperiodline_oper = quotaperiodline[0]
                quotaperiodline_vals = quotaperiodline[2]
                if quotaperiodline_oper == 0:
                    quotaperiodline_vals['pos'] = pos
                    pos = pos + 1

    def _quotaperiodlines_no_repeat(self, vals):
        resp = True
        if vals and 'quotaperiodline_ids' in vals:
            implied_ids = []
            unchanged_ids = []
            for quotaperiodline in vals['quotaperiodline_ids']:
                quotaperiodline_oper = quotaperiodline[0]
                quotaperiodline_id = quotaperiodline[1]
                quotaperiodline_vals = quotaperiodline[2]
                if quotaperiodline_oper == 4 or (quotaperiodline_oper == 1 and
                   'superproduct_id' not in quotaperiodline_vals):
                    unchanged_ids.append(quotaperiodline_id)
                if quotaperiodline_oper == 0 or (quotaperiodline_oper == 1 and
                   'superproduct_id' in quotaperiodline_vals):
                    implied_ids.append(quotaperiodline_vals['superproduct_id'])
            if len(unchanged_ids) > 0:
                filtered_quotaperiodlines = \
                    self.env['wua.quotaperiod.line'].search(
                        [('id', 'in', unchanged_ids)])
                for quotaperiodline in filtered_quotaperiodlines:
                    implied_ids.append(quotaperiodline.superproduct_id.id)
            len_of_implied_ids_original = len(implied_ids)
            if len_of_implied_ids_original > 0:
                implied_ids = list(set(implied_ids))
                len_of_implied_ids_no_repeat = len(implied_ids)
                resp = len_of_implied_ids_original == \
                    len_of_implied_ids_no_repeat
        return resp


class WuaQuotaperiodLine(models.Model):
    _name = 'wua.quotaperiod.line'
    _description = 'Quota-Period Line'
    _order = 'name'

    MAX_SIZE_NAME = 13
    MAX_SIZE_QUOTAPERIODLINE_SUFFIX = 2

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Position',
        required=True,
        default=0)

    pos_str = fields.Char(
        string='Position',
        compute='_compute_pos_str')

    name = fields.Char(
        string='Quota-Period Line',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        ondelete='restrict')

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        required=True,
        default=0)

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    area_total = fields.Float(
        string='Total Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_total')

    volume_total = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume_total')

    configured_line = fields.Boolean(
        string="Configured",
        store=True,
        compute='_compute_configured_line')

    quotaperiodlineparcel_ids = fields.One2many(
        string='Parcels of quota-period line',
        comodel_name='wua.quotaperiod.line.parcel',
        inverse_name='quotaperiodline_id')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota-Period Line.'),
        ('valid_pos', 'CHECK (pos >= 0)',
         'Incorrect Position Value.'),
        ('valid_provision', 'CHECK (provision > 0)',
         'Incorrect Provision Value.'),
        ]

    @api.multi
    def _compute_pos_str(self):
        for record in self:
            pos = record.pos
            if pos:
                record.pos_str = str(pos)
            else:
                record.pos_str = ''

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date', 'pos')
    def _compute_name(self):
        for record in self:
            pos = 0
            initial_date = ''
            if record.quotaperiod_id:
                pos = record.pos
                initial_date = record.quotaperiod_id.initial_date
            record.name = initial_date + '-' + \
                str(pos).zfill(self.MAX_SIZE_QUOTAPERIODLINE_SUFFIX)

    @api.depends('quotaperiodlineparcel_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = 0
            if record.quotaperiodlineparcel_ids:
                number_of_parcels = len(record.quotaperiodlineparcel_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('quotaperiodlineparcel_ids')
    def _compute_area_total(self):
        for record in self:
            area_total = 0
            if record.quotaperiodlineparcel_ids:
                area_total = sum(x.area_official
                                 for x in record.quotaperiodlineparcel_ids)
            record.area_total = area_total

    @api.depends('provision', 'area_total')
    def _compute_volume_total(self):
        for record in self:
            volume_total = record.provision * record.area_total
            record.volume_total = volume_total

    @api.depends('quotaperiodlineparcel_ids')
    def _compute_configured_line(self):
        for record in self:
            configured_line = False
            if record.quotaperiodlineparcel_ids:
                configured_line = True
            record.configured_line = configured_line

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaQuotaperiodLine, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_area = ' (' + area_measurement_name.lower() + ')'
            suffix_provision = ' (m3/' + area_measurement_name.lower() + ')'
            if view_type == 'form':
                for node in doc.xpath("//field[@name='area_total']"):
                    original_label = \
                        self._get_value_from_translation(
                            'base_wua_quota_management',
                            self.__class__.area_total.string)
                    node.set('string', original_label + suffix_area)
                for node in doc.xpath("//field[@name='provision']"):
                    original_label = \
                        self._get_value_from_translation(
                            'base_wua_quota_management',
                            self.__class__.provision.string)
                    node.set('string', original_label + suffix_provision)
            for node in doc.xpath("//field[@name='area_total']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.area_total.string)
                node.set('string', original_label + suffix_area)
            for node in doc.xpath("//field[@name='provision']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.provision.string)
                node.set('string', original_label + suffix_provision)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_select_quotaperiod_line_parcels(self):
        self.ensure_one()
        # Provisional
        print "action_select_quotaperiod_line_parcels"
        # if not self.configured_line:
        #     self.populate_items_select()
        # data_items_select = self.get_data_items_select(self.product_id.name)
        # if data_items_select:
        #     if ('name' in data_items_select and
        #        'res_model' in data_items_select):
        #         if (data_items_select['name'] != '' and
        #            data_items_select['res_model'] != ''):
        #             act_window = {
        #                 'type': 'ir.actions.act_window',
        #                 'name': data_items_select['name'],
        #                 'res_model': data_items_select['res_model'],
        #                 'view_type': 'form',
        #                 'view_mode': 'tree',
        #                 'domain': [["invoicesetline_id", "=", self.id]],
        #                 'limit': 10000000,
        #                 }
        #             return act_window

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp


class WuaQuotaperiodLineParcel(models.Model):
    _name = 'wua.quotaperiod.line.parcel'
    _description = 'Parcel of a quota-period line'
    _order = 'quotaperiodline_id,parcel_id'

    SIZE_CADASTRAL_REFERENCE = 14

    quotaperiodline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.quotaperiod.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    parcel_id = fields.Many2one(
        string='Code',
        comodel_name='wua.parcel',
        required=True,
        ondelete='restrict')

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=SIZE_CADASTRAL_REFERENCE)

    is_billable_water = fields.Boolean(
        string='Billable Water', default=True)

    is_billable_expenses = fields.Boolean(
        string='Billable Expenses', default=True)

    leased_parcel = fields.Boolean(
        string='Leased Parcel', default=False)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    hydraulic_infrastructure_type = fields.Selection([
        (0, 'No infrastructure'),
        (1, 'Pressurized Irrigation'),
        (2, 'Gravity Irrigation'),
        (3, 'Pressurized and Gravity fed Irrigation'),
        ], string='Infrastructure',
        default=0)

    pressurized_irrigation_right = fields.Boolean(
        string="Water Right (pres)",
        default=True)

    gravityfed_irrigation_right = fields.Boolean(
        string="Water Right (grav)",
        default=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    with_watering_shift = fields.Boolean(
        string="With Watering Shift",
        default=True)

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker",
        default=False)

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        ondelete='restrict')

    tag_ids = fields.Many2many(
        string='Parcel Tags',
        comodel_name='wua.parceltag',
        relation='wua_quotaperiod_line_parcel_parceltag_rel',
        column1='quotaperiod_line_parcel_id', column2='parceltag_id',
        ondelete='cascade')

    @api.multi
    def add_to_quotaperiod(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_quotaperiod(self):
        vals = {
            'selected': False,
            }
        self.write(vals)
