# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaReportrequest(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.reportrequest'
    _description = 'Entity (irrigation-report request)'
    _order = 'name'

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
        domain=[('is_wua_partner', '=', True)],
        default=_default_partner_id)

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

    name = fields.Char(
        string="Report-Request Code",
        size=36,
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
        comodel_name='wua.parcel',
        index=True,
        domain="[('partner_id', '=', partner_id)]",
        ondelete='set null')

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    hours = fields.Float(
        string='Hours',
        digits=(32, 4),
        default=0,
        required=True)

    notes = fields.Html(
        string='Notes')

    signature_image = fields.Binary(
        string='Signature')

    irrigationreport_id = fields.Many2one(
        string='Irrigation Report',
        comodel_name='wua.irrigationreport',
        index=True,
        ondelete='restrict')

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
        ('unique_name', 'UNIQUE (name)', 'Existing report request name.')
        ]

    @api.depends('agriculturalseason_id',
                 'agriculturalseason_id.active_agriculturalseason')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            record.of_active_agriculturalseason = \
                record.agriculturalseason_id.active_agriculturalseason

    @api.depends('request_date', 'partner_id', 'product_id', 'product_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.request_date and record.partner_id and record.product_id:
                name = record.request_date + '/' + \
                    str(record.partner_id.partner_code).zfill(6) + '/' + \
                    record.product_id.name
            record.name = name

    @api.depends('irrigationreport_id')
    def _compute_mapped_to_irrigationreport(self):
        for record in self:
            mapped_to_irrigationreport = False
            if record.irrigationreport_id:
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

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.request_date and record.partner_id and record.product_id:
                request_date_str = datetime.datetime.strptime(
                    record.request_date, '%Y-%m-%d').strftime('%x')
                partner_name = record.partner_id.name + ' ' + \
                    '[' + str(record.partner_id.partner_code) + ']'
                language = record.partner_id.lang
                product = \
                    record.with_context({'lang': language}).product_id.name
                name = request_date_str + ' - ' + partner_name + ' - ' + \
                    product
            result.append((record.id, name))
        return result

    @api.multi
    def validate_reportrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'draft' and (not request.cancelled):
            new_irrigationreport = self._add_irrigation_report_from_request(
                request)
            if not new_irrigationreport:
                raise exceptions.UserError(_(
                    'It is not possible to validate the request: the '
                    'indicated type of water does not appear in any intake.'))
            request.irrigationreport_id = new_irrigationreport
            request.state = 'validated'

    @api.multi
    def reset_reportrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'validated':
            if request.irrigationreport_id:
                if request.irrigationreport_id.state == 'validated':
                    raise exceptions.UserError(
                        _('The associated irrigation report is already '
                          'validated. It is not possible to return the draft '
                          'state.'))
                associated_irr_report = \
                    self.env['wua.irrigationreport'].browse(
                        request.irrigationreport_id.id)
                request.write({'irrigationreport_id': False})
                associated_irr_report.unlink()
            request.state = 'draft'

    @api.multi
    def cancel_reportrequest(self):
        self.ensure_one()
        request = self
        if request.state == 'draft' and (not request.cancelled):
            request.cancelled = True

    @api.multi
    def reactivate_reportrequest(self):
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
        res = super(WuaReportrequest, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        hours_sexagesimal = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'hours_sexagesimal')
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if data_in_hours:
                for node in doc.xpath("//field[@name='volume']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"invisible": true}')
                if not hours_sexagesimal:
                    for node in doc.xpath("//field[@name='hours']"):
                        node.set('widget', '')
            else:
                for node in doc.xpath("//field[@name='hours']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(doc)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            if data_in_hours:
                for node in doc.xpath("//field[@name='volume']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
                if not hours_sexagesimal:
                    for node in doc.xpath("//field[@name='hours']"):
                        node.set('widget', '')
            else:
                for node in doc.xpath("//field[@name='hours']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, vals):
        if (self.is_portal_user and not self.env['ir.values'].get_default(
           'wua.configuration', 'wua_portal_user_can_edit')):
            raise exceptions.UserError(_(
                'You do not have permission to edit a report request.'))
        return super(WuaReportrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1 and self.is_portal_user:
            if (not self.env['ir.values'].get_default(
               'wua.configuration', 'wua_portal_user_can_edit')):
                raise exceptions.UserError(_(
                    'You do not have permission to edit a report request.'))
            if ('state' in vals and vals['state'] == 'validated' or
               'state' not in vals and self.state == 'validated'):
                raise exceptions.UserError(_(
                    'A portal user cannot modify a validated report request.'))
        return super(WuaReportrequest, self).write(vals)

    def _add_irrigation_report_from_request(self, request):
        resp = None
        report_initial_time = datetime.datetime.today().strftime('%Y-%m-%d')
        notes = ""
        if request.notes:
            notes = _('<b>Notes from report request:</b><br\\>') + \
                request.notes
        if request.intake_id:
            resp = self.env['wua.irrigationreport'].create({
                'intake_id': request.intake_id.id,
                'product_id': request.product_id.id,
                'report_initial_time': report_initial_time,
                'report_end_time': report_initial_time,
                'partner_id': request.partner_id.id,
                'parcel_id': request.parcel_id.id,
                'end_volume': request.volume,
                'hours': request.hours,
                'notes': notes,
                'partner_signature': request.signature_image,
                })
        return resp

    def validate_reportrequests(self, active_reportrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        reportrequests = \
            self.env['wua.reportrequest'].browse(active_reportrequests)
        for reportrequest in reportrequests:
            reportrequest.validate_reportrequest()

    def reset_reportrequests(self, active_reportrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        reportrequests = \
            self.env['wua.reportrequest'].browse(active_reportrequests)
        for reportrequest in reportrequests:
            reportrequest.reset_reportrequest()

    def cancel_reportrequests(self, active_reportrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        reportrequests = \
            self.env['wua.reportrequest'].browse(active_reportrequests)
        for reportrequest in reportrequests:
            reportrequest.cancel_reportrequest()

    def reactivate_reportrequests(self, active_reportrequests):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(
                _('You do not have permission to execute this action.'))
        reportrequests = \
            self.env['wua.reportrequest'].browse(active_reportrequests)
        for reportrequest in reportrequests:
            reportrequest.reactivate_reportrequest()
