# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval
from lxml import etree


class WuaPreswatering(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.preswatering'
    _description = 'Entity (preswatering)'
    _order = 'agriculturalseason_id, preswateringperiod_id, number'

    MAX_SIZE_NUMBER = 4
    MAX_SIZE_NAME = 12 + MAX_SIZE_NUMBER
    MAX_SIZE_DESCRIPTION = 255

    preswateringperiod_id = fields.Many2one(
        string='Preswatering Period',
        comodel_name='wua.preswateringperiod',
        required=True,
        index=True,
        ondelete='restrict',
    )

    number = fields.Integer(
        string='Watering Number',
        required=True,
        default=1,
    )

    name = fields.Char(
        string='Preswatering',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True,
    )

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION,
        index=True,
    )

    initial_time = fields.Datetime(
        default=lambda self: fields.datetime.now(),
        string='Initial Time',
        required=True,
    )

    preswateringperiod_id = fields.Many2one(
        string='Preswatering Period',
        comodel_name='wua.preswateringperiod',
        required=True,
        index=True,
        ondelete='restrict',
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id',
        ondelete='restrict',
    )

    is_open = fields.Boolean(
        string='Open',
        store=True,
        compute='_compute_is_open',
        index=True,
    )

    state = fields.Selection([
        ('01_draft', 'Draft'),
        ('02_calculated', 'Calculated'),
        ('03_validated', 'Validated'),
        ], string='Request state',
        index=True,
        default='01_draft',
    )

    preswatering_initial_time = fields.Datetime(
        string='Preswatering Start Time',
        index=True,
    )

    preswatering_end_time = fields.Datetime(
        string='Preswatering End Time',
        store=True,
        compute='_compute_preswatering_end_time',
    )

    preswatering_duration = fields.Integer(
        string='Preswatering Time (min)',
        default=0,
    )

    nominal_flow_requested = fields.Float(
        string='Nominal Flow Requested (m³/h)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_requested',
    )

    nominal_flow_ls_requested = fields.Float(
        string='Nominal Flow Requested (l/s)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_ls_requested',
    )

    nominal_flow_granted = fields.Float(
        string='Nominal Flow Granted (m³/h)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_granted',
    )

    nominal_flow_ls_granted = fields.Float(
        string='Nominal Flow Granted (l/s)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_ls_granted',
    )

    nominal_flow_issued = fields.Float(
        string='Nominal Flow Issued (m³/h)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_issued',
    )

    nominal_flow_ls_issued = fields.Float(
        string='Nominal Flow Issued (l/s)',
        digits=(32, 4),
        store=True,
        compute='_compute_nominal_flow_ls_issued',
    )

    preswatering_volume = fields.Float(
        string='Preswatering Vol. Requested (m³)',
        digits=(32, 4),
        store=True,
        compute='_compute_preswatering_volume',
    )

    preswatering_volume_granted = fields.Float(
        string='Preswatering Vol. Granted (m³)',
        digits=(32, 4),
        store=True,
        compute='_compute_preswatering_volume_granted',
    )

    preswatering_volume_issued = fields.Float(
        string='Preswatering Vol. Issued (m³)',
        digits=(32, 4),
        store=True,
        compute='_compute_preswatering_volume_issued',
    )

    presresconsumption_ids = fields.One2many(
        string='Presres Consumptions',
        comodel_name='wua.presresconsumption',
        inverse_name='preswatering_id',
    )

    number_of_presresconsumptions = fields.Integer(
        string='Number of presresconsumptions',
        store=True,
        compute='_compute_number_of_presresconsumptions',
    )

    initialized = fields.Boolean(
        string='Initialized',
        default=False,
    )

    presresconsumptions_issued = fields.Boolean(
        string='Presresconsumptions Issued',
        default=False,
    )

    notes = fields.Html(
        string='Notes',
    )

    condition_line_ids = fields.One2many(
        string='Condition Lines',
        comodel_name='wua.preswatering.condition.line',
        inverse_name='preswatering_id',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Preswatering.'),
        ('positive_number', 'CHECK (number > 0)',
         'The preswatering number must be a positive value.'),
        ]

    @api.constrains('initial_time', 'preswateringperiod_id')
    def _check_initial_time_within_period(self):
        for record in self:
            if record.initial_time and record.preswateringperiod_id:
                period = record.preswateringperiod_id
                initial_date = fields.Datetime.from_string(
                    record.initial_time).strftime('%Y-%m-%d')
                if not (period.initial_date <= initial_date <=
                        period.end_date):
                    raise exceptions.ValidationError(_(
                        'The start date of the preswatering (%s) must be '
                        'within the period (%s - %s).') % (
                            record.initial_time,
                            period.initial_date,
                            period.end_date,
                        ),
                    )

    @api.depends('preswateringperiod_id', 'number')
    def _compute_name(self):
        for record in self:
            value = ''
            if (record.preswateringperiod_id and record.number > 0):
                value = record.preswateringperiod_id.name + '-' + \
                    str(record.number).zfill(
                        self.MAX_SIZE_NUMBER)
            record.name = value

    @api.depends('preswateringperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.preswateringperiod_id:
                agriculturalseason_id = \
                    record.preswateringperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('preswateringperiod_id', 'preswateringperiod_id.state')
    def _compute_is_open(self):
        for record in self:
            is_open = False
            if record.preswateringperiod_id and \
                    record.preswateringperiod_id.state == '01_open':
                is_open = True
            record.is_open = is_open

    @api.depends('preswatering_initial_time', 'preswatering_duration')
    def _compute_preswatering_end_time(self):
        for record in self:
            preswatering_end_time = None
            if record.preswatering_initial_time:
                preswatering_end_time = record.preswatering_initial_time
                if (record.preswatering_duration):
                    preswatering_end_time = fields.Datetime.from_string(
                        record.preswatering_initial_time) + \
                        timedelta(minutes=record.preswatering_duration)
            record.preswatering_end_time = preswatering_end_time

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.watering_volume')
    def _compute_preswatering_volume(self):
        for record in self:
            preswatering_volume = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    preswatering_volume += presresconsumption.watering_volume
            record.preswatering_volume = preswatering_volume

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.watering_volume_granted')
    def _compute_preswatering_volume_granted(self):
        for record in self:
            preswatering_volume_granted = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    preswatering_volume_granted += \
                        presresconsumption.watering_volume_granted
            record.preswatering_volume_granted = preswatering_volume_granted

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.watering_volume_issued')
    def _compute_preswatering_volume_issued(self):
        for record in self:
            preswatering_volume_issued = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    preswatering_volume_issued += \
                        presresconsumption.watering_volume_issued
            record.preswatering_volume_issued = preswatering_volume_issued

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow')
    def _compute_nominal_flow_requested(self):
        for record in self:
            nominal_flow_requested = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_requested += presresconsumption.nominal_flow
            record.nominal_flow_requested = nominal_flow_requested

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow_ls')
    def _compute_nominal_flow_ls_requested(self):
        for record in self:
            nominal_flow_ls_requested = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_ls_requested += \
                        presresconsumption.nominal_flow_ls
            record.nominal_flow_ls_requested = nominal_flow_ls_requested

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow_granted')
    def _compute_nominal_flow_granted(self):
        for record in self:
            nominal_flow_granted = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_granted += \
                        presresconsumption.nominal_flow_granted
            record.nominal_flow_granted = \
                nominal_flow_granted

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow_ls_granted')
    def _compute_nominal_flow_ls_granted(self):
        for record in self:
            nominal_flow_ls_granted = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_ls_granted += \
                        presresconsumption.nominal_flow_ls_granted
            record.nominal_flow_ls_granted = \
                nominal_flow_ls_granted

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow_issued')
    def _compute_nominal_flow_issued(self):
        for record in self:
            nominal_flow_issued = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_issued += \
                        presresconsumption.nominal_flow_issued
            record.nominal_flow_issued = \
                nominal_flow_issued

    @api.depends('presresconsumption_ids',
                 'presresconsumption_ids.nominal_flow_ls_issued')
    def _compute_nominal_flow_ls_issued(self):
        for record in self:
            nominal_flow_ls_issued = 0
            for presresconsumption in record.presresconsumption_ids:
                if presresconsumption.selected:
                    nominal_flow_ls_issued += \
                        presresconsumption.nominal_flow_ls_issued
            record.nominal_flow_ls_issued = \
                nominal_flow_ls_issued

    @api.depends('presresconsumption_ids')
    def _compute_number_of_presresconsumptions(self):
        for record in self:
            record.number_of_presresconsumptions = \
                len(record.presresconsumption_ids)

    # No summary for: number, wateringtime_perunitarea and volume_perunitime.
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'number' in fields:
            fields.remove('number')
        return super(WuaPreswatering, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].\
                transform_date_to_locale(
                    record.preswateringperiod_id.initial_date)
            number_str = str(record.number)
            name = initial_date_str + ' - ' + number_str
            result.append((record.id, name))
        return result

    # A preswatering can't be deleted if there are issued consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            issued_presresconsumptions = \
                record.presresconsumption_ids.filtered(
                    lambda x: x.state == '03_issued')
            if issued_presresconsumptions:
                raise exceptions.UserError(_(
                    'You cannot delete a preswatering if there are '
                    'issued consumptions.'))
            if record.presresconsumption_ids:
                presresconsumption_vals = {
                    'state': '01_proposed',
                    'nominal_flow_granted': 0,
                    'nominal_flow_ls_granted': 0,
                    'nominal_flow_issued': 0,
                    'nominal_flow_ls_issued': 0,
                }
                record.presresconsumption_ids.write(presresconsumption_vals)
        return super(WuaPreswatering, self).unlink()

    @api.multi
    def action_see_presresconsumptions(self):
        self.ensure_one()
        presresconsumption_ids = \
            [x.id for x in self.presresconsumption_ids
             if x.selected]
        if len(presresconsumption_ids) > 0:
            condition = [('id', 'in', presresconsumption_ids)]
            id_tree_view = self.env.ref(
                'base_wua_pressurized_irrigation_request.'
                'wua_presresconsumption_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_pressurized_irrigation_request.'
                'wua_presresconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_pressurized_irrigation_request.'
                'wua_presresconsumption_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Presresconsumptions'),
                'res_model': 'wua.presresconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                }
            return act_window
        else:
            raise exceptions.UserError(_(
                'There are no consumptions to show.'))

    @api.multi
    def cancel_preswatering(self):
        self.ensure_one()
        presresconsumptions_to_select_ids = self.presresconsumption_ids.mapped(
            lambda x: x.id)
        self.presresconsumption_ids.write(
            {
                'state': '01_proposed',
                'preswatering_id': None,
                'nominal_flow_granted': 0,
                'nominal_flow_ls_granted': 0,
                'nominal_flow_issued': 0,
                'nominal_flow_ls_issued': 0,
                'selected': False,
            },
        )
        self.initialized = False
        self.presresconsumptions_issued = False
        self.state = '01_draft'
        self.select_presresconsumptions()
        self.presresconsumption_ids.filtered(lambda x: x.rejected).write(
            {'rejected': False})
        presresconsumptions_to_unselect = self.presresconsumption_ids.filtered(
            lambda x: x.id not in presresconsumptions_to_select_ids)
        presresconsumptions_to_unselect.write({'selected': False})

    @api.multi
    def select_presresconsumptions(self):
        self.ensure_one()
        if not self.initialized:
            num_presresconsumptions = self.\
                join_presresconsumptions_to_preswatering()
            if num_presresconsumptions > 0:
                self.initialized = True
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_request.'
            'wua_presresconsumption_to_select_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_request.'
            'wua_presresconsumption_to_select_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Selection of presresconsumption for the calculation '
                      'process'),
            'res_model': 'wua.presresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': [["preswatering_id", "=", self.id]],
            'limit': 10000000,
            'context': {'from_preswatering': True},
        }
        return act_window

    def join_presresconsumptions_to_preswatering(self):
        num_presresconsumptions_by_request = \
            self.join_presresconsumptions_to_preswatering_by_request()
        resp = num_presresconsumptions_by_request
        return resp

    def join_presresconsumptions_to_preswatering_by_request(self):
        resp = 0
        # Get only preswatering from the same day or later
        initial_time = self.initial_time
        condition = [
            ('preswateringperiod_id', '=', self.preswateringperiod_id.id),
            ('preswatering_id', '=', False),
            ('preswateringrequest_id.state', '=', '02_validated'),
            ('request_time', '>', initial_time),
        ]
        condition = self._update_condition(condition)
        presresconsumptions = self.env['wua.presresconsumption'].search(
            condition)
        if presresconsumptions:
            presresconsumptions.write({
                'preswatering_id': self.id,
                'selected': True,
                })
            resp = len(presresconsumptions)
        return resp

    # Hook: This method is called from descendant classes to refine
    def _process_granted_nominal_flows(
            self, presresconsumptions, preswatering):
        for presresconsumption in presresconsumptions:
            presresconsumption.write({
                'nominal_flow_granted': presresconsumption.nominal_flow,
                'nominal_flow_ls_granted': presresconsumption.nominal_flow_ls,
            })

    # Hook: This method is called from descendant classes to refine
    def _process_issued_nominal_flows(self, presresconsumptions, preswatering):
        for presresconsumption in presresconsumptions:
            presresconsumption.write({
                'nominal_flow_issued': presresconsumption.nominal_flow_granted,
                'nominal_flow_ls_issued':
                    presresconsumption.nominal_flow_ls_granted,
            })
        return True

    def update_conditions(self):
        for line in self.condition_line_ids:
            field = line.condition_id.field_to_check.name
            operator = line.condition_id.comparison_operator
            value_to_check = line.check_value
            grouped_value = 0.0
            group_operator = line.condition_id.group_operator
            waterconnections = line.condition_id.waterconnection_ids
            presresconsumptions = self.env['wua.presresconsumption'].search(
                [('preswatering_id', '=', self.id),
                 ('selected', '=', True),
                 ('waterconnection_id', 'in', waterconnections.ids)])
            if group_operator == 'sum':
                grouped_value = sum(
                    presresconsumptions.mapped(lambda x: x[field]))
            # Check if the operator between value_to_check and grouped_value
            # is true and then state == '02_ok', in other case 03_not_ok
            expression = "%s %s %s" % (grouped_value, operator, value_to_check)
            condition_state = '02_ok'
            try:
                result = safe_eval(expression)
                if not result:
                    condition_state = '03_not_ok'
            except Exception:
                condition_state = '03_not_ok'
            condition_vals = {
                'result_value': grouped_value,
                'state': condition_state,
            }
            line.write(condition_vals)

    @api.multi
    def calculate_presresconsumptions(self):
        self.ensure_one()
        presresconsumptions = self.env['wua.presresconsumption'].search(
            [('preswatering_id', '=', self.id),
             ('selected', '=', True)])
        self.condition_line_ids
        if presresconsumptions:
            # Assign the granted flow
            self._process_granted_nominal_flows(presresconsumptions, self)
            # Update the watering initial time and duration
            min_request_time = None
            max_request_time = None
            max_duration = 0
            for presresconsumption in presresconsumptions:
                request_time = presresconsumption.request_time
                watering_duration = presresconsumption.watering_duration or 0
                if min_request_time is None or request_time < min_request_time:
                    min_request_time = request_time
                if max_request_time is None or request_time > max_request_time:
                    max_request_time = request_time
                    max_duration = watering_duration
            # Init time is the earliest petition
            watering_initial_time = fields.Datetime.from_string(
                min_request_time)
            # End time is the latest petition + max duration
            watering_end_time = fields.Datetime.from_string(
                max_request_time) + timedelta(hours=max_duration)
            preswatering_duration = int(
                (watering_end_time -
                 watering_initial_time).total_seconds() / 60)
            watering_vals = {
                'preswatering_initial_time': watering_initial_time,
                'preswatering_duration': preswatering_duration,
                'state': '02_calculated',
                }
            self.write(watering_vals)
            self.update_conditions()

    @api.multi
    def validate_presresconsumptions(self):
        self.ensure_one()
        conditions_not_met = self.condition_line_ids.filtered(
            lambda x: x.state == '03_not_ok' and x.condition_id.is_mandatory)
        if (len(conditions_not_met) > 0):
            raise exceptions.UserError(_(
                'The conditions %s are not met.') %
                ', '.join(conditions_not_met.mapped('condition_id.name')))
        presresconsumptions_to_unjoin = \
            self.env['wua.presresconsumption'].search(
                [('preswatering_id', '=', self.id),
                 ('selected', '=', False)])
        if presresconsumptions_to_unjoin:
            presresconsumption_vals = {
                'rejected': True,
                'preswatering_id': None,
                }
            presresconsumptions_to_unjoin.write(presresconsumption_vals)
        self.presresconsumption_ids.write({
            'state': '02_granted',
        })
        self.state = '03_validated'

    @api.multi
    def issue_presresconsumptions(self):
        self.ensure_one()
        presresconsumptions_to_issue = \
            self.env['wua.presresconsumption'].search(
                [('preswatering_id', '=', self.id),
                 ('selected', '=', True),
                 ('rejected', '=', False),
                 ('state', '=', '02_granted')])
        issue_correct = self._process_issued_nominal_flows(
            presresconsumptions_to_issue, self)
        if (issue_correct):
            presresconsumptions_to_issue.write({
                'state': '03_issued',
            })
            self.presresconsumptions_issued = True
        # Don't Raise, we need message posts to inform the user
        # TODO: Now hooks will inform the user but should we also inform
        # the user here? Issue always gonna be correct here if not further
        # modules are installed.
        # else:
        #     raise exceptions.UserError(_(
        #         'There was an error issuing the consumptions.'))

    # Hook: This method is called from descendant classes to refine
    # the condition to find presres-consumptions in the
    # "join_presresconsumptions_to_watering_by_request" method.
    def _update_condition(self, condition):
        resp = condition
        return resp

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaPreswatering, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second',
        )
        doc = etree.XML(res['arch'])
        field_visibility = {
            'nominal_flow_requested': not use_flow_ls,
            'nominal_flow_ls_requested': use_flow_ls,
            'nominal_flow_granted': not use_flow_ls,
            'nominal_flow_ls_granted': use_flow_ls,
            'nominal_flow_issued': not use_flow_ls,
            'nominal_flow_ls_issued': use_flow_ls,
        }
        if view_type in ['form', 'tree']:
            for field, visible in field_visibility.items():
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set('invisible', '0' if visible else '1')
                    node.set(
                        'modifiers',
                        ('{"readonly": true, "tree_invisible": false, '
                         '"invisible": false}'
                         if visible
                         else '{"readonly": true, "tree_invisible": true, '
                              '"invisible": true}'),
                    )
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class WuaPreswateringCondition(models.Model):

    _name = 'wua.preswatering.condition'
    _description = 'Entity (preswatering condition)'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )

    field_to_check = fields.Many2one(
        string='Field to Check',
        comodel_name='ir.model.fields',
        required=True,
        ondelete='restrict',
        domain="[('model_id', '=', 'wua.presresconsumption')]",
    )

    comparison_operator = fields.Selection(
        [
            ('=', '='),
            ('!=', '!='),
            ('>', '>'),
            ('<', '<'),
            ('>=', '>='),
            ('<=', '<='),
        ],
        string='Operator',
        required=True,
    )

    value = fields.Float(
        string='Value',
        required=True,
    )

    group_operator = fields.Selection(
        [
            ('sum', 'Sum'),
        ],
        string='Group Operator',
        required=True,
    )

    waterconnection_ids = fields.Many2many(
        comodel_name='wua.waterconnection',
        relation='wua_preswatering_condition_waterconnection_rel',
        column1='condition_id',
        column2='waterconnection_id',
        string='Water Connections',
    )

    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=True,
    )


class WuaPreswateringConditionLine(models.Model):

    _name = 'wua.preswatering.condition.line'
    _description = 'Entity (preswatering condition line)'
    _order = 'sequence'

    preswatering_id = fields.Many2one(
        string='Preswatering',
        comodel_name='wua.preswatering',
        required=True,
        ondelete='cascade',
    )

    condition_id = fields.Many2one(
        string='Condition',
        comodel_name='wua.preswatering.condition',
        required=True,
        ondelete='restrict',
    )

    state = fields.Selection(
        [
            ('01_not_checked', 'Not Checked'),
            ('02_ok', 'Ok'),
            ('03_not_ok', 'Not Ok'),
        ],
        string='State',
        default='01_not_checked',
    )

    check_value = fields.Float(
        string='Check Value',
        compute='_compute_check_value',
        store=True,
    )

    result_value = fields.Float(
        string='Result Value',
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default=1,
    )

    @api.depends('condition_id', 'condition_id.value')
    def _compute_check_value(self):
        for record in self:
            check_value = 0.0
            if record.condition_id and record.condition_id.value:
                check_value = record.condition_id.value
            record.check_value = check_value
