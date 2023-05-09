# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _
from lxml import etree


class WuaIrrigationsrequest(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.irrigationsrequest'
    _description = 'Entity (irrigations request)'
    _order = 'irrigationsrequest_number,name'

    @api.model
    def default_get(self, fields):
        res = super(WuaIrrigationsrequest, self).default_get(fields)
        intake_id = False
        product_id = False
        intakes = self.env['wua.intake'].search([])
        products = self.env['product.product'].search(
            [('categ_id.productcategory_code', '=', 11)])
        if (len(intakes) == 1):
            intake_id = intakes[0].id
        if (len(products) == 1):
            product_id = products[0].id
        if product_id:
            res['product_id'] = product_id
        if intake_id:
            res['intake_id'] = intake_id
        return res

    def _default_partner_id(self):
        resp = None
        user = self.env.user
        if user.has_group('base_wua.group_wua_portal_user'):
            partner = self.env['res.partner'].browse(user.partner_id.id)
            if partner and partner.is_wua_partner:
                resp = partner.id
        return resp

    def _default_agriculturalseason_id(self):
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        return active_agricultural_season

    def _default_is_portal_user(self):
        resp = None
        user = self.env.user
        if user.has_group('base_wua.group_wua_portal_user'):
            resp = True
        return resp

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_partner_id,
        domain=[('is_wua_partner', '=', True)])

    request_date = fields.Date(
        string='Request Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    agriculturalseason_id = fields.Many2one(
        string="Agricultural Season",
        readonly=True,
        index=True,
        required=True,
        default=_default_agriculturalseason_id,
        comodel_name="wua.agriculturalseason",
        ondelete="set null")

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        required=True,
        index=True,
        ondelete='restrict')

    irrigationsrequest_number = fields.Integer(
        string="Irrigationsrequest Number",
        store=True,
        compute="_compute_irrigationsrequest_number_code")

    irrigationsrequest_code = fields.Char(
        string="Irrigations-Request Code",
        size=28,
        store=True,
        index=True,
        compute="_compute_irrigationsrequest_number_code")

    # Size = partner.zfill(6) + '-' + parcel (20) + '-' + date (10)
    name = fields.Char(
        string="Irrigations-Request Code",
        size=39,
        store=True,
        index=True,
        compute="_compute_name")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated')],
        string="State",
        default="draft",
        requred=True)

    cancelled = fields.Boolean(
        string="Cancelled",
        default=False)

    parcel_id = fields.Many2one(
        string='Parcel',
        required=True,
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict')

    irrigationreport_ids = fields.One2many(
        string='Irrigation Reports',
        comodel_name='wua.irrigationreport',
        inverse_name='irrigationsrequest_id')

    number_of_irrigations = fields.Integer(
        string='Number of irrigations',
        required=True,
        index=True,
        default=1,)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        store=True,
        related='parcel_id.area_official')

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume')

    notes = fields.Html(
        string='Notes')

    signature_image = fields.Binary(
        string='Signature')

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        index=True,
        ondelete='restrict',
        required=True)

    mapped_to_irrigationreport = fields.Boolean(
        string='Mapped to a irrigation report',
        store=True,
        compute='_compute_mapped_to_irrigationreport')

    is_portal_user = fields.Boolean(
        string='Created by the partner',
        default=_default_is_portal_user,
        compute='_compute_is_portal_user')

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        readonly=True)

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id')

    credit_overdue = fields.Monetary(
        string='Overdue Receivable',
        compute='_compute_credit_overdue',
        help="Overdue amount this customer owes you.")

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing irrigations request name.'),
        ('number_of_irrigations',
         'CHECK (number_of_irrigations > 0)',
         'The number of irrigations must be a value greater than zero.')
        ]

    @api.depends('agriculturalseason_id',
                 'agriculturalseason_id.active_agriculturalseason')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            record.of_active_agriculturalseason = \
                record.agriculturalseason_id.active_agriculturalseason

    @api.depends('agriculturalseason_id')
    def _compute_irrigationsrequest_number_code(self):
        for record in self:
            irrigationsrequest_number = 1
            irrigationsrequest_code = ''
            if record.agriculturalseason_id:
                initial_date = record.agriculturalseason_id.initial_date
                end_date = record.agriculturalseason_id.end_date
                agriculturalseason = record.agriculturalseason_id
                if record.id:
                    last_request = self.env['wua.irrigationsrequest'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ('id', '!=', record.id)],
                        order='irrigationsrequest_number desc', limit=1)
                else:
                    last_request = self.env['wua.irrigationsrequest'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ],
                        order='irrigationsrequest_number desc', limit=1)
                if last_request:
                    irrigationsrequest_number = \
                        last_request[0].irrigationsrequest_number + 1
                irrigationsrequest_code = initial_date + '/' + end_date + \
                    '/' + str(irrigationsrequest_number).zfill(6)
            record.irrigationsrequest_number = irrigationsrequest_number
            record.irrigationsrequest_code = irrigationsrequest_code

    @api.depends('request_date', 'partner_id', 'parcel_id', 'parcel_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.request_date and record.partner_id and record.parcel_id:
                name = str(record.partner_id.partner_code).zfill(6) + '-' + \
                    record.parcel_id.name + '-' + record.request_date
            record.name = name

    @api.depends('irrigationreport_ids')
    def _compute_mapped_to_irrigationreport(self):
        for record in self:
            mapped_to_irrigationreport = False
            if (record.irrigationreport_ids and
                    len(record.irrigationreport_ids) > 0):
                mapped_to_irrigationreport = True
            record.mapped_to_irrigationreport = mapped_to_irrigationreport

    @api.depends('partner_id')
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.depends('partner_id', 'currency_id')
    def _compute_credit_overdue(self):
        for record in self:
            credit_overdue = 0
            if (record.partner_id and record.currency_id):
                credit_overdue = record.partner_id.credit_overdue
            record.credit_overdue = credit_overdue

    @api.depends('area_official', 'number_of_irrigations')
    def _compute_volume(self):
        volume_perunitarea = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'volume_perunitarea')
        for record in self:
            volume = 0
            if (record.area_official and record.number_of_irrigations):
                volume = record.area_official * volume_perunitarea * \
                    record.number_of_irrigations
            record.volume = volume

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.request_date and record.partner_id and record.parcel_id:
                request_date_str = datetime.datetime.strptime(
                    record.request_date, '%Y-%m-%d').strftime('%x')
                partner_name = record.partner_id.name + ' ' + \
                    '[' + str(record.partner_id.partner_code) + ']'
                name = partner_name + ' - ' + record.parcel_id.name + ' - ' + \
                    request_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def validate_irrigationsrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'draft' and (not request.cancelled):
            if (not request.agriculturalseason_id.active_agriculturalseason):
                raise exceptions.UserError(
                    _('Cannot validate irrigationsrequest of non active '
                      'agriculturalseason.'))
            # Ids list of new irrigationreports
            new_irrigationreports = self._add_irrigation_reports_from_request(
                request)
            if not new_irrigationreports:
                raise exceptions.UserError(_(
                    'It is not possible to validate the request.'))
            request.state = 'validated'

    @api.multi
    def reset_irrigationsrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'validated' and request.irrigationreport_ids:
            if (not request.agriculturalseason_id.active_agriculturalseason):
                raise exceptions.UserError(
                    _('Cannot reset irrigationsrequest of non active '
                      'agriculturalseason.'))
            for report in request.irrigationreport_ids:
                if report.state == 'validated':
                    raise exceptions.UserError(
                        _('Some associated irrigation report is already '
                          'validated. It is not possible to return the '
                          'draft state.'))
                associated_report = self.env['wua.irrigationreport'].\
                    browse(report.id)
                associated_report.with_context(
                    {'resetting': True}).unlink()
            request.state = 'draft'

    @api.multi
    def cancel_irrigationsrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'draft' and (not request.cancelled):
            request.cancelled = True

    @api.multi
    def reactivate_irrigationsrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'draft' and request.cancelled:
            request.cancelled = False

    @api.multi
    def _compute_is_portal_user(self):
        for record in self:
            is_portal_user = False
            if self.env.user.has_group('base_wua.group_wua_portal_user'):
                is_portal_user = True
            record.is_portal_user = is_portal_user

    @api.constrains('parcel_id')
    def _check_parcel_id(self):
        if (len(self) == 1 and self.parcel_id and
           self.parcel_id.partner_id != self.partner_id):
            raise exceptions.UserError(
                _('The partner must be the irrigator of the parcel.'))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationsrequest, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            else:
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.sudo().env['wua.parcel'].\
                        get_value_from_translation(
                            'base_wua_irrigations_request',
                            self.__class__.area_official.string)
                    node.set('string', original_label +
                             ' (' + _('ha') + ')')
            if area_measurement_name != '':
                area_measurement_name = ' (' + \
                    area_measurement_name.lower() + ')'
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.sudo().env['wua.parcel'].\
                        get_value_from_translation(
                            'base_wua_irrigations_request',
                            self.__class__.area_official.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, vals):
        if (self.is_portal_user and not self.env['ir.values'].get_default(
           'wua.configuration', 'wua_portal_user_can_edit')):
            raise exceptions.UserError(_(
                'You do not have permission to edit an irrigations request.'))
        return super(WuaIrrigationsrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1 and self.is_portal_user:
            if (not self.env['ir.values'].get_default(
               'wua.configuration', 'wua_portal_user_can_edit')):
                raise exceptions.UserError(_(
                    'You do not have permission to edit an irrigations '
                    'request.'))
            if ('state' in vals and vals['state'] == 'validated' or
               'state' not in vals and self.state == 'validated'):
                raise exceptions.UserError(_(
                    'A portal user cannot modify a validated irrigations '
                    'request.'))
        return super(WuaIrrigationsrequest, self).write(vals)

    @api.multi
    def action_see_irrigation_reports(self):
        self.ensure_one()
        if self.irrigationreport_ids:
            id_tree_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_form').id
            search_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Irrigation Reports'),
                'res_model': 'wua.irrigationreport',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.irrigationreport_ids.ids)]
                }
            return act_window

    def get_area_measurement_name(self):
        area_measurement_name = _('ha')
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode('utf_8')
        return area_measurement_name

    def _add_irrigation_reports_from_request(self, request):
        report_initial_time = datetime.datetime.today().strftime('%Y-%m-%d')
        notes = ""
        resp = []
        if request.notes:
            notes = _('<b>Notes from irrigations request:</b><br\\>') + \
                request.notes
        if request.intake_id:
            volume_per_report = request.volume / request.number_of_irrigations
            for i in range(request.number_of_irrigations):
                resp.append(self.env['wua.irrigationreport'].create({
                    'irrigationsrequest_id': request.id,
                    'intake_id': request.intake_id.id,
                    'product_id': request.product_id.id,
                    'report_initial_time': report_initial_time,
                    'report_end_time': report_initial_time,
                    'partner_id': request.partner_id.id,
                    'parcel_id': request.parcel_id.id,
                    'end_volume': volume_per_report,
                    'notes': notes,
                    'partner_signature': request.signature_image,
                    }).id)
        return resp

    def validate_irrigationsrequests(self, active_irrigationsrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        irrigationsrequests = \
            self.env['wua.irrigationsrequest'].browse(
                active_irrigationsrequests)
        for irrigationsrequest in irrigationsrequests:
            irrigationsrequest.validate_irrigationsrequest()

    def reset_irrigationsrequests(self, active_irrigationsrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        irrigationsrequests = \
            self.env['wua.irrigationsrequest'].browse(
                active_irrigationsrequests)
        for irrigationsrequest in irrigationsrequests:
            irrigationsrequest.reset_irrigationsrequest()

    def cancel_irrigationsrequests(self, active_irrigationsrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        irrigationsrequests = \
            self.env['wua.irrigationsrequest'].browse(
                active_irrigationsrequests)
        for irrigationsrequest in irrigationsrequests:
            irrigationsrequest.cancel_irrigationsrequest()

    def reactivate_irrigationsrequests(self, active_irrigationsrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        irrigationsrequests = \
            self.env['wua.irrigationsrequest'].browse(
                active_irrigationsrequests)
        for irrigationsrequest in irrigationsrequests:
            irrigationsrequest.reactivate_irrigationsrequest()
