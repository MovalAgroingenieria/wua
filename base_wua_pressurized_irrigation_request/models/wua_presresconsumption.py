# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import pytz
from lxml import etree
from datetime import timedelta, datetime
from odoo import models, fields, api, _, exceptions


class WuaPresresconsumption(models.Model):
    _name = 'wua.presresconsumption'
    _inherit = 'mail.thread'
    _description = 'Request Consumption'
    _order = 'request_time'

    name = fields.Char(
        string='Code',
        compute='_compute_name',
        store=True,
        index=True,
    )

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='restrict',
        index=True,
    )

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        compute='_compute_irrigationshed_id',
        store=True,
        ondelete='restrict',
        index=True,
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        compute='_compute_hydraulicsector_id',
        store=True,
        ondelete='restrict',
        index=True,
    )

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        compute='_compute_waterpipe_id',
        store=True,
        ondelete='restrict',
        index=True,
    )

    preswateringperiod_id = fields.Many2one(
        string='Period',
        comodel_name='wua.preswateringperiod',
        required=True,
        ondelete='restrict',
        index=True,
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        compute='_compute_agriculturalseason_id',
        store=True,
        index=True,
        ondelete='restrict',
    )

    preswateringrequest_id = fields.Many2one(
        string='Request',
        comodel_name='wua.preswateringrequest',
        ondelete='cascade',
        index=True,
    )

    preswatering_id = fields.Many2one(
        string='Preswatering',
        comodel_name='wua.preswatering',
        ondelete='set null',
        index=True,
    )

    state = fields.Selection(
        string='Consumption State',
        selection=[
            ('01_proposed', 'Proposed'),
            ('02_granted', 'Granted'),
            ('03_issued', 'Issued'),
        ],
        default='01_proposed',
        index=True,
    )

    watering_duration = fields.Float(
        string='Watering Duration (Hours)',
        digits=(32, 4),
        required=True,
    )

    nominal_flow = fields.Float(
        string='Nominal Flow Requested (m³/h)',
        digits=(32, 4),
        required=True,
        default=0.0,
    )

    nominal_flow_ls = fields.Float(
        string='Nominal Flow Requested (l/s)',
        digits=(32, 4),
        default=0.0,
    )

    nominal_flow_granted = fields.Float(
        string='Nominal Flow Granted (m³/h)',
        digits=(32, 4),
        readonly=True,
        default=0.0,
    )

    nominal_flow_ls_granted = fields.Float(
        string='Nominal Flow Granted (l/s)',
        digits=(32, 4),
        readonly=True,
        default=0.0,
    )

    nominal_flow_issued = fields.Float(
        string='Nominal Flow Issued (m³/h)',
        digits=(32, 4),
        readonly=True,
        default=0.0,
        track_visibility='onchange',
    )

    nominal_flow_ls_issued = fields.Float(
        string='Nominal Flow Issued (l/s)',
        digits=(32, 4),
        readonly=True,
        default=0.0,
        track_visibility='onchange',
    )

    watering_volume = fields.Float(
        string='Requested Volume',
        compute='_compute_watering_volume',
        store=True,
        digits=(32, 4),
    )

    watering_volume_granted = fields.Float(
        string='Granted Volume',
        compute='_compute_watering_volume_granted',
        store=True,
        digits=(32, 4),
    )

    watering_volume_issued = fields.Float(
        string='Issued Volume',
        compute='_compute_watering_volume_issued',
        store=True,
        digits=(32, 4),
    )

    initial_hour = fields.Float(
        string='Requested Start Hour',
        required=True,
    )

    total_affected_area_official_hec = fields.Float(
        string='Affected Area (Hectares)',
        compute='_compute_total_affected_area',
        store=True,
        digits=(32, 4),
    )

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        compute='_compute_data_from_wateringrequest',
        store=True,
    )

    is_portal_user = fields.Boolean(
        string='Created by Irrigator',
        compute='_compute_data_from_wateringrequest',
        store=True,
    )

    rejected = fields.Boolean(
        string='Rejected',
        default=False,
    )

    selected = fields.Boolean(
        string='Selected',
        default=True,
    )

    partner_id = fields.Many2one(
        string='Irrigator',
        comodel_name='res.partner',
        compute='_compute_partner_id',
        store=True,
    )

    request_time = fields.Datetime(
        string='Request Time',
        compute='_compute_request_time',
        store=True,
    )

    request_date = fields.Date(
        string='Request Date',
        compute='_compute_request_date',
        store=True,
    )

    modification_deadline = fields.Datetime(
        string="Modification Deadline",
        compute="_compute_modification_deadline",
        store=True,
        help="The deadline before which modifications are allowed for this"
             "request.",
    )

    modification_deadline_message = fields.Text(
        string="Modification Message",
        compute="_compute_modification_deadline_message",
    )

    portal_can_modify = fields.Boolean(
        string='Editable by Irrigator',
        compute='_compute_portal_can_modify',
    )

    waterconnection_id_domain = fields.Char(
        compute="_compute_waterconnection_id_domain",
        readonly=True,
        store=False,
    )

    calendar_display_name = fields.Char(
        string="Calendar Display Name",
        compute="_compute_calendar_display_name",
        store=False,
    )

    issued_presresconumption_manual_edit = fields.Boolean(
        string='Issued consumption modified',
        default=False,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)',
            'The consumption code must be unique.'),
        ('non_negative_duration', 'CHECK (watering_duration >= 0)',
            'The duration must be a non-negative value.'),
    ]

    @api.onchange('waterconnection_id')
    def _onchange_waterconnection_id(self):
        # Get the default duration fo the waterconnection
        # if not default duration on WC, then check global parameter
        irrigation_duration = 0
        global_irrigation_duration = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration', 'default_irrigation_duration')
        if (self.waterconnection_id):
            irrigation_duration = \
                self.waterconnection_id.default_request_duration
        if (not irrigation_duration and global_irrigation_duration):
            irrigation_duration = global_irrigation_duration
        # Get the default initial hour fo the waterconnection
        # if not initial hour duration on WC, then check global parameter
        initial_hour = 0.0
        global_initial_hour = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'default_presresconsumption_initial_hour')
        if (self.waterconnection_id):
            initial_hour = \
                self.waterconnection_id.default_request_initial_hour
        if (not initial_hour and global_initial_hour):
            initial_hour = global_initial_hour
        nominal_flow = 0
        if (self.waterconnection_id and self.waterconnection_id.watermeter_id):
            nominal_flow = \
                self.waterconnection_id.watermeter_id.nominal_water_flow
        self.nominal_flow = nominal_flow
        self.watering_duration = irrigation_duration
        self.initial_hour = initial_hour

    @api.onchange('nominal_flow_ls_issued')
    def _onchange_nominal_flow_ls_issued(self):
        self.issued_presresconumption_manual_edit = True

    @api.depends(
        'preswateringrequest_id', 'preswateringrequest_id.name',
        'waterconnection_id', 'initial_hour')
    def _compute_name(self):
        for record in self:
            name = ''
            preswateringrequest_name = record.preswateringrequest_id.name
            waterconnection_name = record.waterconnection_id.name
            initial_hour = record.initial_hour
            if preswateringrequest_name and waterconnection_name:
                name = u"{}-{}-{}".format(
                    preswateringrequest_name,
                    waterconnection_name,
                    initial_hour,
                )
            record.name = name

    @api.depends(
        'partner_id', 'waterconnection_id', 'watering_volume')
    def _compute_calendar_display_name(self):
        for record in self:
            calendar_display_name = u''
            if (record.partner_id and record.waterconnection_id):
                calendar_display_name = record.partner_id.name + u' - ' + \
                    record.waterconnection_id.name + u' - ' + \
                    str((record.watering_volume or 0.0)) + u' m³'
            record.calendar_display_name = calendar_display_name

    @api.depends('preswateringrequest_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if (record.preswateringrequest_id and
                    record.preswateringrequest_id.partner_id):
                partner_id = record.preswateringrequest_id.partner_id
            record.partner_id = partner_id

    @api.depends('preswateringrequest_id',
                 'preswateringrequest_id.agriculturalseason_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if (record.preswateringrequest_id and
                    record.preswateringrequest_id.agriculturalseason_id):
                agriculturalseason_id = \
                    record.preswateringrequest_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('waterconnection_id',
                 'waterconnection_id.irrigationshed_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            irrigationshed_id = None
            if (record.waterconnection_id and
                    record.waterconnection_id.irrigationshed_id):
                irrigationshed_id = \
                    record.waterconnection_id.irrigationshed_id
            record.irrigationshed_id = irrigationshed_id

    @api.depends('irrigationshed_id',
                 'irrigationshed_id.waterpipe_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if (record.irrigationshed_id and
                    record.irrigationshed_id.waterpipe_id):
                waterpipe_id = \
                    record.irrigationshed_id.waterpipe_id
            record.waterpipe_id = waterpipe_id

    @api.depends('irrigationshed_id',
                 'irrigationshed_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if (record.irrigationshed_id and
                    record.irrigationshed_id.hydraulicsector_id):
                hydraulicsector_id = \
                    record.irrigationshed_id.hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.depends('watering_duration', 'nominal_flow')
    def _compute_watering_volume(self):
        for record in self:
            watering_volume = 0
            if (record.watering_duration and record.nominal_flow):
                watering_volume = record.watering_duration * \
                    record.nominal_flow
            record.watering_volume = watering_volume

    @api.depends('watering_duration', 'nominal_flow_granted')
    def _compute_watering_volume_granted(self):
        for record in self:
            watering_volume_granted = 0
            if (record.watering_duration and record.nominal_flow_granted):
                watering_volume_granted = record.watering_duration * \
                    record.nominal_flow_granted
            record.watering_volume_granted = watering_volume_granted

    @api.depends('watering_duration', 'nominal_flow_issued')
    def _compute_watering_volume_issued(self):
        for record in self:
            watering_volume_issued = 0
            if (record.watering_duration and record.nominal_flow_issued):
                watering_volume_issued = record.watering_duration * \
                    record.nominal_flow_issued
            record.watering_volume_issued = watering_volume_issued

    @api.depends('waterconnection_id')
    def _compute_total_affected_area(self):
        for record in self:
            total_affected_area = 0
            if(record.waterconnection_id and
                    record.waterconnection_id.
                    total_affected_area_official_hec):
                total_affected_area = \
                    record.waterconnection_id.total_affected_area_official_hec
            record.total_affected_area_official_hec = total_affected_area

    @api.depends('preswateringrequest_id', 'preswateringrequest_id.user_id',
                 'preswateringrequest_id.is_portal_user')
    def _compute_data_from_wateringrequest(self):
        for record in self:
            user_id = None
            is_portal_user = False
            if record.preswateringrequest_id:
                user_id = record.preswateringrequest_id.user_id
                is_portal_user = record.preswateringrequest_id.is_portal_user
            record.user_id = user_id
            record.is_portal_user = is_portal_user

    @api.depends(
        'preswateringrequest_id', 'preswateringrequest_id.initial_date',
        'initial_hour')
    def _compute_request_time(self):
        for record in self:
            request_time = None
            user_tz = 'Europe/Madrid'
            if (self.env.user and self.env.user.tz):
                user_tz = self.env.user.tz
            if (record.preswateringrequest_id.initial_date):
                initial_date = fields.Date.from_string(
                    record.preswateringrequest_id.initial_date)
                hours = int(record.initial_hour)
                minutes = int(round((record.initial_hour - hours) * 60))
                initial_time = timedelta(hours=hours, minutes=minutes)
                local_datetime = datetime.combine(
                    initial_date, datetime.min.time()) + initial_time
                user_timezone = pytz.timezone(user_tz)
                local_datetime = user_timezone.localize(local_datetime)
                request_time = local_datetime.astimezone(pytz.utc)
            record.request_time = request_time

    @api.depends('request_time')
    def _compute_request_date(self):
        for record in self:
            request_date = None
            if (record.request_time):
                request_date = fields.Datetime.from_string(record.request_time)
                request_date = request_date.strftime('%Y-%m-%d')
            record.request_date = request_date

    @api.depends('request_time')
    def _compute_modification_deadline(self):
        lock_modification_hours = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'lock_modification_hours')
        for record in self:
            modification_deadline = None
            if (record.request_time):
                modification_deadline = fields.Datetime.from_string(
                    record.request_time) - \
                    timedelta(hours=int(lock_modification_hours))
            record.modification_deadline = modification_deadline

    @api.depends('modification_deadline')
    def _compute_modification_deadline_message(self):
        for record in self:
            modification_deadline_message = ''
            if record.modification_deadline:
                deadline = fields.Datetime.from_string(
                    record.modification_deadline)
                user_tz = 'Europe/Madrid'
                if (self.env.user and self.env.user.tz):
                    user_tz = self.env.user.tz
                user_timezone = pytz.timezone(user_tz)
                local_deadline = pytz.utc.localize(deadline)
                localize_deadline = local_deadline.astimezone(user_timezone)
                formatted_deadline = localize_deadline.strftime(
                    '%d/%m/%Y %H:%M')
                modification_deadline_message = _(
                    'Modifications allowed until {}').format(
                    formatted_deadline)
            record.modification_deadline_message = \
                modification_deadline_message

    @api.multi
    def _compute_portal_can_modify(self):
        now = fields.Datetime.now()
        for record in self:
            portal_can_modify = False
            if (record.modification_deadline):
                portal_can_modify = record.modification_deadline > now
            record.portal_can_modify = portal_can_modify

    @api.multi
    def set_as_selected(self, active_presresconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            presresconsumptions = self.env['wua.presresconsumption'].browse(
                active_presresconsumptions)
            for record in presresconsumptions:
                if record.state == '01_proposed':
                    vals = {
                        'selected': True,
                        }
                    record.write(vals)

    @api.multi
    def set_as_unselected(self, active_presresconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            presresconsumptions = self.env['wua.presresconsumption'].browse(
                active_presresconsumptions)
            for record in presresconsumptions:
                if record.state == '01_proposed':
                    vals = {
                        'selected': False,
                        }
                    record.write(vals)

    @api.model
    def create(self, vals):
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second')
        if 'preswateringrequest_id' in vals:
            preswateringrequest_id = vals['preswateringrequest_id']
            if preswateringrequest_id:
                preswateringrequest = \
                    self.env['wua.preswateringrequest'].browse(
                        preswateringrequest_id)
                if preswateringrequest:
                    vals['preswateringperiod_id'] = \
                        preswateringrequest.preswateringperiod_id.id
        flow_field_pairs = {
            'nominal_flow': 'nominal_flow_ls',
            'nominal_flow_granted': 'nominal_flow_ls_granted',
            'nominal_flow_issued': 'nominal_flow_ls_issued',
        }
        for m3h_field, ls_field in flow_field_pairs.items():
            if use_flow_ls and ls_field in vals:
                vals[m3h_field] = vals[ls_field] * 3.6
            elif not use_flow_ls and m3h_field in vals:
                vals[ls_field] = vals[m3h_field] / 3.6
        return super(WuaPresresconsumption, self).create(vals)

    @api.multi
    def write(self, vals):
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second')
        flow_field_pairs = {
            'nominal_flow': 'nominal_flow_ls',
            'nominal_flow_granted': 'nominal_flow_ls_granted',
            'nominal_flow_issued': 'nominal_flow_ls_issued',
        }
        for m3h_field, ls_field in flow_field_pairs.items():
            if use_flow_ls and ls_field in vals:
                vals[m3h_field] = vals[ls_field] * 3.6
            elif not use_flow_ls and m3h_field in vals:
                vals[ls_field] = vals[m3h_field] / 3.6
        return super(WuaPresresconsumption, self).write(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if (not self._context.get('force_remove') and
                    (record.state == '02_granted' or
                        record.state == '03_issued')):
                raise exceptions.UserError(_(
                    'You cannot delete a presresconsumption in a granted or '
                    'issued state. First you must delete the watering.'))
        return super(WuaPresresconsumption, self).unlink()

    @api.model
    def _get_waterconnection_id_domain(self):
        result = []
        if self.partner_id:
            self.env.cr.execute("""
                SELECT wc.id
                FROM wua_parcel_irrigationpoint ip
                JOIN wua_waterconnection wc
                ON wc.id = ip.waterconnection_id
                WHERE ip.partner_id = %s AND ip.type = 'WC'
                GROUP BY wc.id
            """, (self.partner_id.id,))
            result = self.env.cr.fetchall()
        return [('id', 'in', result)]

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaPresresconsumption, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second',
        )
        doc = etree.XML(res['arch'])
        field_visibility = {
            'nominal_flow': not use_flow_ls,
            'nominal_flow_ls': use_flow_ls,
            'nominal_flow_granted': not use_flow_ls,
            'nominal_flow_ls_granted': use_flow_ls,
            'nominal_flow_issued': not use_flow_ls,
            'nominal_flow_ls_issued': use_flow_ls,
        }
        if view_type in ['form', 'tree']:
            for field, visible in field_visibility.items():
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set('invisible', '0' if visible else '1')
                    modifiers = node.get('modifiers')
                    if modifiers:
                        modifiers_dict = json.loads(modifiers)
                    else:
                        modifiers_dict = {}
                    modifiers_dict['tree_invisible'] = not visible
                    modifiers_dict['invisible'] = not visible
                    node.set('modifiers', json.dumps(modifiers_dict))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        # Now check the toolbar for avoiding select or unselect on not
        # preswatering view
        from_preswatering = self.env.context.get('from_preswatering', False)
        if toolbar and not from_preswatering:
            actions = res.get('toolbar', {}).get('action', [])
            filtered_actions = [
                action for action in actions
                if action.get('xml_id') not in [
                    'base_wua_pressurized_irrigation_request.'
                    'wua_set_presresconsumption_as_selected',
                    'base_wua_pressurized_irrigation_request.'
                    'wua_set_presresconsumption_as_unselected',
                ]
            ]
            res['toolbar']['action'] = filtered_actions
        return res

    @api.multi
    @api.depends('partner_id', 'waterconnection_id')
    def _compute_waterconnection_id_domain(self):
        for record in self:
            domain = record._get_waterconnection_id_domain()
            record.waterconnection_id_domain = json.dumps(domain)
