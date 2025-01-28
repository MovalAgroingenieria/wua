# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
import json
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaIrrigationReport(models.Model):
    _name = 'wua.irrigationreport'
    _description = "WUA Irrigation Report"
    _order = "name"

    def _default_agriculturalseason_id(self):
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        return active_agricultural_season

    def _default_volume_time_equivalence(self):
        resp = 0.0
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if (active_agricultural_season):
            resp = active_agricultural_season.volume_time_equivalence
        else:
            default_volume_time_equivalence = self.env['ir.values'].\
                get_default('wua.configuration', 'volume_time_equivalence')
            if default_volume_time_equivalence:
                resp = default_volume_time_equivalence
        return resp

    def _default_volume_time_equivalence_ls(self):
        resp = self._default_volume_time_equivalence() / 3.6
        return resp

    report_initial_time = fields.Datetime(
        string='Start Time',
        required=True,
        index=True)

    report_end_time = fields.Datetime(
        string='End Time',
        required=True,
        index=True)

    intake_id = fields.Many2one(
        string="Intake",
        required=True,
        index=True,
        comodel_name="wua.intake",
        ondelete="restrict",
        domain=[('valid_for_irrigationreports', '=', True)])

    agriculturalseason_id = fields.Many2one(
        string="Agricultural Season",
        readonly=True,
        index=True,
        required=True,
        default=_default_agriculturalseason_id,
        comodel_name="wua.agriculturalseason",
        ondelete="set null")

    irrigationreport_number = fields.Integer(
        string="Report Number",
        store=True,
        compute="_compute_irrigationreport_number_name")

    name = fields.Char(
        string="Report Code",
        size=36,
        store=True,
        index=True,
        compute="_compute_irrigationreport_number_name")

    partner_id = fields.Many2one(
        string="WUA Partner",
        required=True,
        index=True,
        domain="[('is_wua_partner', '=', True)]",
        comodel_name="res.partner",
        ondelete="restrict")

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        readonly=True)

    initial_volume = fields.Float(
        string='Initial Value (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    end_volume = fields.Float(
        string='Final Value (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    hours = fields.Float(
        string='Hours',
        digits=(32, 4),
        default=0,
        required=True)

    conversion_factor = fields.Float(
        string='Conversion Factor',
        digits=(32, 4),
        default=1,
        required=True)

    volume_time_equivalence = fields.Float(
        string='Flow (m³/h)',
        digits=(32, 4),
        default=_default_volume_time_equivalence,
        required=True,
    )

    volume_time_equivalence_ls = fields.Float(
        string='Flow (l/s)',
        digits=(32, 4),
        default=_default_volume_time_equivalence_ls,
        required=True,
    )

    volume = fields.Float(
        string='Gross Value (m³)',
        digits=(32, 4),
        store=True,
        compute="_compute_volume")

    adjustement_volume = fields.Float(
        string='Adjust. Value (m³)',
        digits=(32, 4),
        required=True,
        default=0)

    volume_real = fields.Float(
        string='Real Volume (m³)',
        digits=(32, 4),
        store=True,
        compute="_compute_volume_real")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated')],
        string="State",
        default="draft",
        required=True)

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    notes = fields.Html(string='Notes')

    partner_signature = fields.Binary(
        string='Signature')

    delivery_note = fields.Integer(
        string='Delivery Note',
        store=True,
        index=True,
        compute='_compute_delivery_note')

    delivery_note_str = fields.Char(
        string='Delivery Note',
        size=25)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict',
        domain="[('partner_id', '=', partner_id)]",
    )

    watermeter_id = fields.Many2one(
        string='Watermeter',
        comodel_name='wua.watermeter',
        index=True,
        ondelete='restrict',
        domain="[('waterconnection_id.irrigationpoint_ids.partner_id', "
               "'=', partner_id)]",
    )

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker",
        default=False)

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        index=True,
        ondelete='restrict',
        domain=[('is_irrigation_worker', '=', True)])
    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id')

    credit_overdue = fields.Monetary(
        compute='_compute_credit_overdue',
        string='Overdue Receivable',
        help="Overdue amount this customer owes you.")

    cancelled = fields.Boolean(
        string="Irrigationreport Cancelled",
        default=False)

    _sql_constraints = [
        ('valid_irrigationreport_time_range',
         'CHECK (report_initial_time <= report_end_time)',
         'The initial time is after the end time.'),
        ('unique_name',
         'UNIQUE (name)',
         'Existing report code.'),
        ('valid_initial_volume',
         'CHECK (initial_volume >= 0)',
         'The initial volume can not be a negative value.'),
        ('valid_end_volume',
         'CHECK (end_volume >= initial_volume)',
         'The final volume must be equal or greather than initial volume.'),
        ('valid_hours',
         'CHECK (hours >= 0)',
         'The number of hours can not be a negative value.'),
        ('valid_delivery_note',
         'CHECK (delivery_note >= 0)',
         'The delivery note must be 0 or a greater number'),
        ('valid_volume_time_equivalence',
         'CHECK (volume_time_equivalence >= 0)',
         'The custom flow be 0 or a greater number'),
        ('valid_volume_time_equivalence_ls',
         'CHECK (volume_time_equivalence_ls >= 0)',
         'The custom flow be 0 or a greater number'),
        ]

    @api.constrains('delivery_note_str')
    def _check_delivery_note_str(self):
        if (self.delivery_note_str):
            no_positive_number = False
            try:
                delivery_note = int(self.delivery_note_str)
                if (delivery_note < 0):
                    no_positive_number = True
            except Exception:
                no_positive_number = True
            if (no_positive_number):
                raise exceptions.ValidationError(_('The delivery note must be'
                                                   ' 0 or a greater number'))

    @api.depends('report_initial_time', 'report_end_time', 'intake_id',
                 'agriculturalseason_id')
    def _compute_irrigationreport_number_name(self):
        for record in self:
            irrigationreport_number = 1
            name = ''
            if record.agriculturalseason_id and record.intake_id:
                initial_date = record.agriculturalseason_id.initial_date
                end_date = record.agriculturalseason_id.end_date
                intake = record.intake_id
                agriculturalseason = record.agriculturalseason_id
                if record.id:
                    last_report = self.env['wua.irrigationreport'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ('intake_id', '=', intake.id),
                         ('id', '!=', record.id)],
                        order='irrigationreport_number desc', limit=1)
                else:
                    last_report = self.env['wua.irrigationreport'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ('intake_id', '=', intake.id)],
                        order='irrigationreport_number desc', limit=1)
                if last_report:
                    irrigationreport_number = \
                        last_report[0].irrigationreport_number + 1
                name = initial_date + '/' + end_date + '/' + \
                    str(intake.intake_code).zfill(6) + '/' + \
                    str(irrigationreport_number).zfill(6)
            record.irrigationreport_number = irrigationreport_number
            record.name = name

    @api.depends(
        'initial_volume', 'end_volume', 'hours', 'conversion_factor',
        'volume_time_equivalence', 'volume_time_equivalence_ls')
    def _compute_volume(self):
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        agriculturalseasons = self.env['wua.agriculturalseason']
        custom_irrigationreport_flow = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'custom_irrigationreport_flow')
        custom_irrigationreport_flow_ls = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'custom_irrigationreport_flow_ls')
        for record in self:
            volume = 0
            if data_in_hours:
                if custom_irrigationreport_flow:
                    if custom_irrigationreport_flow_ls:
                        volume_time_equivalence = \
                            record.volume_time_equivalence_ls * 3.6
                    else:
                        volume_time_equivalence = \
                            record.volume_time_equivalence
                else:
                    agriculturalseason = agriculturalseasons.browse(
                        record.agriculturalseason_id.id)
                    volume_time_equivalence = \
                        agriculturalseason[0].volume_time_equivalence * \
                        record.conversion_factor
                volume = record.hours * volume_time_equivalence
            else:
                volume = record.end_volume - record.initial_volume
            if volume < 0:
                volume = 0
            record.volume = volume

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('agriculturalseason_id',
                 'agriculturalseason_id.active_agriculturalseason')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            record.of_active_agriculturalseason = \
                record.agriculturalseason_id.active_agriculturalseason

    @api.depends('delivery_note_str')
    def _compute_delivery_note(self):
        for record in self:
            delivery_note = 0
            if (record.delivery_note_str):
                delivery_note = int(record.delivery_note_str)
            record.delivery_note = delivery_note

    @api.onchange('partner_id')
    def _change_partner_id(self):
        if self.agriculturalseason_id and self.intake_id and self.partner_id:
            data_in_hours = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'data_in_hours')
            watermeter_management = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'watermeter_management')
            if not data_in_hours and not watermeter_management:
                last_report = self.env['wua.irrigationreport'].search(
                    [('agriculturalseason_id', '=',
                      self.agriculturalseason_id.id),
                     ('intake_id', '=', self.intake_id.id)],
                    order='irrigationreport_number desc', limit=1)
                if last_report:
                    end_volume_of_last_record = \
                        last_report[0].end_volume
                    self.initial_volume = end_volume_of_last_record

    @api.onchange('report_initial_time', 'report_end_time')
    def _change_hours(self):
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        hours = self.hours
        if (data_in_hours and self.report_initial_time and
           self.report_end_time):
            initial_time = fields.Datetime.from_string(
                self.report_initial_time)
            end_time = fields.Datetime.from_string(self.report_end_time)
            hours = (end_time - initial_time).\
                total_seconds() / 3600
        self.hours = hours

    @api.onchange('watermeter_id', 'report_initial_time')
    def _onchange_watermeter_id(self):
        # If watermeter associated to the irrigation report
        # check last irrigationreport and set the initial volume as the
        # end volume of the last irrigation report
        watermeter_management = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'watermeter_management')
        if (watermeter_management and self.watermeter_id and
                self.report_initial_time):
            initial_volume = 0
            search_domain = [('watermeter_id', '=',
                             self.watermeter_id.id),
                             ('report_end_time', '<=',
                             self.report_initial_time)]
            if (self.id):
                search_domain.append(('id', '!=', self.id))
            # Api on change record has no id, but the original
            # can have it
            elif (self._origin and self._origin.id):
                search_domain.append(('id', '!=', self._origin.id))
            last_ireport = self.env['wua.irrigationreport'].search(
                search_domain,
                limit=1, order='report_end_time desc')
            if (last_ireport and last_ireport[0]):
                initial_volume = last_ireport[0].end_volume
            self.initial_volume = initial_volume

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationReport, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        hours_sexagesimal = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'hours_sexagesimal')
        custom_irrigationreport_flow = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'custom_irrigationreport_flow')
        custom_irrigationreport_flow_ls = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'custom_irrigationreport_flow_ls')
        watermeter_management = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'watermeter_management')
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if data_in_hours:
                # Hide 'initial_volume' 'end_volume'
                for field_name in ['initial_volume', 'end_volume']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        modifiers = json.loads(node.get("modifiers", "{}"))
                        modifiers['invisible'] = True
                        node.set('modifiers', json.dumps(modifiers))
                if not hours_sexagesimal:
                    for node in doc.xpath("//field[@name='hours']"):
                        node.attrib.pop('widget', None)
                if custom_irrigationreport_flow:
                    for node in doc.xpath(
                            "//field[@name='conversion_factor']"):
                        modifiers = json.loads(node.get("modifiers", "{}"))
                        modifiers['invisible'] = True
                        node.set('modifiers', json.dumps(modifiers))
                    if custom_irrigationreport_flow_ls:
                        for node in doc.xpath(
                                "//field[@name='volume_time_equivalence']"):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
                    else:
                        for node in doc.xpath(
                                "//field[@name='volume_time_equivalence_ls']"):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
                else:
                    for field_name in ['volume_time_equivalence',
                                       'volume_time_equivalence_ls']:
                        for node in doc.xpath(
                                "//field[@name='%s']" % field_name):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
            else:
                for field_name in [
                        'hours', 'conversion_factor',
                        'volume_time_equivalence',
                        'volume_time_equivalence_ls']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        modifiers = json.loads(node.get("modifiers", "{}"))
                        modifiers['invisible'] = True
                        node.set('modifiers', json.dumps(modifiers))
            if not watermeter_management:
                for node in doc.xpath("//field[@name='watermeter_id']"):
                    modifiers = json.loads(node.get("modifiers", "{}"))
                    modifiers['invisible'] = True
                    node.set('modifiers', json.dumps(modifiers))
            actions_to_remove = [
                'base_wua_irrigation_report.'
                'action_print_irrigation_distribution_report',
            ]
            actions_menu = res.get('toolbar', {}).get('action', [])
            res['toolbar']['action'] = [
                action_menu for action_menu in actions_menu
                if action_menu['xml_id'] not in actions_to_remove
            ]
            res['arch'] = etree.tostring(doc, encoding='unicode')
        elif view_type == 'tree':
            doc = etree.XML(res['arch'])
            if data_in_hours:
                if not hours_sexagesimal:
                    for node in doc.xpath("//field[@name='hours']"):
                        node.attrib.pop('widget', None)
                if custom_irrigationreport_flow:
                    for node in doc.xpath(
                            "//field[@name='conversion_factor']"):
                        modifiers = json.loads(node.get("modifiers", "{}"))
                        modifiers['tree_invisible'] = True
                        node.set('modifiers', json.dumps(modifiers))
                    if custom_irrigationreport_flow_ls:
                        for node in doc.xpath(
                                "//field[@name='volume_time_equivalence']"):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['tree_invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
                    else:
                        for node in doc.xpath(
                                "//field[@name='volume_time_equivalence_ls']"):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['tree_invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
                else:
                    for field_name in [
                            'volume_time_equivalence',
                            'volume_time_equivalence_ls']:
                        for node in doc.xpath(
                                "//field[@name='%s']" % field_name):
                            modifiers = json.loads(node.get("modifiers", "{}"))
                            modifiers['tree_invisible'] = True
                            node.set('modifiers', json.dumps(modifiers))
            else:
                for field_name in [
                        'hours', 'conversion_factor',
                        'volume_time_equivalence',
                        'volume_time_equivalence_ls']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        modifiers = json.loads(node.get("modifiers", "{}"))
                        modifiers['tree_invisible'] = True
                        node.set('modifiers', json.dumps(modifiers))
            if not watermeter_management:
                for node in doc.xpath("//field[@name='watermeter_id']"):
                    modifiers = json.loads(node.get("modifiers", "{}"))
                    modifiers['tree_invisible'] = True
                    node.set('modifiers', json.dumps(modifiers))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.model
    def create(self, vals):
        new_record = super(WuaIrrigationReport, self).create(vals)
        report_initial_time = new_record.report_initial_time
        report_end_time = datetime.datetime.strptime(
            new_record.report_end_time, '%Y-%m-%d %H:%M:%S')
        agriculturalseason = new_record.agriculturalseason_id
        agricultural_initial_date = agriculturalseason.initial_date
        agricultural_end_date = \
            datetime.datetime.strptime(
                agriculturalseason.end_date, '%Y-%m-%d') + \
            datetime.timedelta(hours=23, minutes=59, seconds=59)
        if (report_initial_time < agricultural_initial_date or
           report_end_time > agricultural_end_date):
            raise exceptions.ValidationError(_('The dates of the report '
                                               'are out of the '
                                               'agricultural season.'))
        # Add transformation between conversion factor and
        # volume_time_equivalence
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        if (data_in_hours):
            custom_irrigationreport_flow = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'custom_irrigationreport_flow')
            custom_irrigationreport_flow_ls = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'custom_irrigationreport_flow_ls')
            if (custom_irrigationreport_flow):
                conversion_factor = 0
                # Check if value is in /s or in m³/h
                if (custom_irrigationreport_flow_ls):
                    new_record.volume_time_equivalence = \
                        new_record.volume_time_equivalence_ls * 3.6
                else:
                    new_record.volume_time_equivalence_ls = \
                        new_record.volume_time_equivalence / 3.6
                # Conversion factor Always relation with m³/h
                if (agriculturalseason.volume_time_equivalence):
                    conversion_factor = new_record.volume_time_equivalence / \
                        agriculturalseason.volume_time_equivalence
                new_record.conversion_factor = conversion_factor
            else:
                new_record.volume_time_equivalence = \
                    new_record.conversion_factor * \
                    agriculturalseason.volume_time_equivalence
                # m³ /h -> l/s
                new_record.volume_time_equivalence_ls = \
                    new_record.volume_time_equivalence / 3.6
        return new_record

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            data_in_hours = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'data_in_hours')
            if (data_in_hours):
                custom_irrigationreport_flow = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'custom_irrigationreport_flow')
                custom_irrigationreport_flow_ls = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'custom_irrigationreport_flow_ls')
                # If custom flow check if is in l/s or in m³/h
                # Then transform to the other units and then the conversion
                # factor
                if (custom_irrigationreport_flow):
                    if (custom_irrigationreport_flow_ls and
                            'volume_time_equivalence_ls' in vals):
                        volume_time_equivalence = \
                            vals['volume_time_equivalence_ls'] * 3.6
                        conversion_factor = volume_time_equivalence / \
                            self.agriculturalseason_id.volume_time_equivalence
                        vals.update({
                            'conversion_factor': conversion_factor,
                            'volume_time_equivalence': volume_time_equivalence,
                        })
                    elif (not custom_irrigationreport_flow_ls and
                            'volume_time_equivalence' in vals):
                        volume_time_equivalence_ls = \
                            vals['volume_time_equivalence'] / 3.6
                        conversion_factor = vals['volume_time_equivalence'] / \
                            self.agriculturalseason_id.volume_time_equivalence
                        vals.update({
                            'conversion_factor': conversion_factor,
                            'volume_time_equivalence_ls':
                                volume_time_equivalence_ls,
                        })
                # Conversion factor -> volume_time_equivalence -> vte_ls
                elif ('conversion_factor' in vals):
                    volume_time_equivalence = \
                        self.agriculturalseason_id.volume_time_equivalence * \
                        vals['conversion_factor']
                    volume_time_equivalence_ls = volume_time_equivalence / 3.6
                    vals.update({
                        'volume_time_equivalence': volume_time_equivalence,
                        'volume_time_equivalence_ls':
                            volume_time_equivalence_ls,
                    })
                super(WuaIrrigationReport, self).write(vals)
            else:
                super(WuaIrrigationReport, self).write(vals)
        else:
            super(WuaIrrigationReport, self).write(vals)
        return True

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['irrigationreport_number', 'initial_volume',
                            'end_volume']
        for field_to_remove in fields_to_remove:
            if field_to_remove in fields:
                fields.remove(field_to_remove)
        return super(WuaIrrigationReport, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def validate_irrigationreport(self):
        self.ensure_one()
        self.state = 'validated'

    @api.multi
    def cancel_irrigationreport(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def change_to_active(self):
        self.ensure_one()
        self.cancelled = False

    @api.multi
    def change_to_cancelled(self):
        self.ensure_one()
        self.cancelled = True

    @api.multi
    def set_as_active(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if irrigationreport.cancelled:
                irrigationreport.change_to_active()

    @api.multi
    def set_as_cancelled(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if (not irrigationreport.cancelled and
               not irrigationreport.state == 'executed'):
                irrigationreport.change_to_cancelled()

    @api.depends('partner_id', 'currency_id')
    def _compute_credit_overdue(self):
        for record in self:
            credit_overdue = 0
            if (record.partner_id and record.currency_id):
                credit_overdue = record.partner_id.credit_overdue
            record.credit_overdue = credit_overdue

    @api.depends('partner_id')
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    def validate_irrigationreports(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if irrigationreport.state == 'draft':
                irrigationreport.validate_irrigationreport()

    def cancel_irrigationreports(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if irrigationreport.state == 'validated':
                irrigationreport.cancel_irrigationreport()

    # For reports
    def _get_data_in_hours(self):
        return self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')

    # For reports
    def _get_hours_sexagesimal(self):
        return self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'hours_sexagesimal')
