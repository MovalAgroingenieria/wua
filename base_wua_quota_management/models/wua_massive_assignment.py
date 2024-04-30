# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaMassiveAssignments(models.Model):
    _name = 'wua.massive.assignments'
    _description = 'Massive Assignments'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_REASON = 75
    MAX_SIZE_NAME = 25 + MAX_SIZE_SUPERPRODUCT_CODE + MAX_SIZE_REASON

    def _default_agriculturalseason_id(self):
        resp = 0
        proposed_agriculturalseason_id = \
            self.env.context.get('agriculturalseason_id', False)
        if proposed_agriculturalseason_id:
            resp = proposed_agriculturalseason_id
        else:
            active_agriculturalseason = \
                (self.env['wua.agriculturalseason'].
                 get_active_agriculturalseason())
            if active_agriculturalseason:
                resp = active_agriculturalseason.id
        return resp

    def _default_quotaperiod_id(self):
        resp = 0
        proposed_quotaperiod_id = \
            self.env.context.get('quotaperiod_id', False)
        if proposed_quotaperiod_id:
            resp = proposed_quotaperiod_id
        else:
            active_agriculturalseason = \
                (self.env['wua.agriculturalseason'].
                 get_active_agriculturalseason())
            if active_agriculturalseason:
                quotaperiod_model = self.env['wua.quotaperiod']
                current_generated_quotaperiod = \
                    quotaperiod_model.get_current_generated_quotaperiod()
                if (current_generated_quotaperiod and
                   current_generated_quotaperiod.agriculturalseason_id ==
                   active_agriculturalseason):
                    resp = current_generated_quotaperiod.id
                else:
                    filtered_quotaperiods = quotaperiod_model.search(
                        [('agriculturalseason_id', '=',
                          active_agriculturalseason.id),
                         ('state', '=', 'generated'),
                         ('is_closed', '=', False)],
                        order='initial_date', limit=1)
                    if filtered_quotaperiods:
                        resp = filtered_quotaperiods[0].id
                    else:
                        filtered_quotaperiods = quotaperiod_model.search(
                            [('agriculturalseason_id', '=',
                              active_agriculturalseason.id),
                             ('state', '=', 'generated')],
                            order='initial_date', limit=1)
                        if filtered_quotaperiods:
                            resp = filtered_quotaperiods[0].id
        return resp

    def _default_superproduct_id(self):
        resp = 0
        proposed_superproduct_id = \
            self.env.context.get('superproduct_id', False)
        if proposed_superproduct_id:
            resp = proposed_superproduct_id
        return resp

    def _default_category_id(self):
        resp = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            resp = proposed_category.id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_quotaperiod_id)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_superproduct_id)

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        required=True)

    total_assignment_volume = fields.Float(
        string='Total Assignment Volumen (m³)',
        digits=(32, 2),
        compute='_compute_total_assignment_volume')

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        index=True,
        required=True,
        ondelete='restrict',
        default=_default_category_id)

    reason = fields.Char(
        string='Reason',
        default='',
        size=MAX_SIZE_REASON,
        required=True)

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    state = fields.Selection([
        ('00_draft', 'Draft'),
        ('01_executed', 'Executed'),
        ], string='State',
        default='00_draft',
        track_visibility='onchange')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    closed_quotaperiod = fields.Boolean(
        string='Closed Quota Period',
        store=True,
        compute='_compute_closed_quotaperiod')

    name = fields.Char(
        string='Massive Transfer',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    individualinput_ids = fields.One2many(
        string='Individual Inputs',
        comodel_name='wua.individualinput',
        inverse_name='massive_controlled_assignment_id')

    assignment_parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.massive.assignments.parcel',
        inverse_name='massive_controlled_assignment_id')

    selected_parcels = fields.Boolean(
        string='Parcels Already Selected',
        default=False)

    selected_assignment_parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.massive.assignments.parcel',
        inverse_name='massive_controlled_assignment_id',
        domain=[('selected', '=', True)])

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Massive Assignment.'),
    ]

    @api.multi
    def execute_massive_controlled_assignment(self):
        for record in self:
            quotaperiod = record.quotaperiod_id
            data_ok, error_message = record._check_data(quotaperiod)
            if not data_ok:
                raise exceptions.ValidationError(error_message)
            partners_and_provisions = {}
            assignment_parcels = record.selected_assignment_parcel_ids
            for assignment_parcel in assignment_parcels:
                parcel = assignment_parcel.parcel_id
                for partnerlink in parcel.partnerlink_ids:
                    if partnerlink.water_costs_percentage > 0:
                        partner = partnerlink.partner_id.id
                        water_costs = partnerlink.water_costs_percentage / 100
                        provision = \
                            assignment_parcel.assignment_provision_parcel * \
                            water_costs
                        if (partner in partners_and_provisions):
                            partners_and_provisions[partner] = provision + \
                                partners_and_provisions[partner]
                        else:
                            partners_and_provisions[partner] = provision
            model_individualinput = self.env['wua.individualinput']
            for partner, provision in partners_and_provisions.items():
                model_individualinput.create({
                    'agriculturalseason_id':
                        quotaperiod.agriculturalseason_id.id,
                    'quotaperiod_id': quotaperiod.id,
                    'superproduct_id': record.superproduct_id.id,
                    'partner_id': partner,
                    'category_id': record.category_id.id,
                    'event_time': record.event_time,
                    'volume': provision,
                    'reason': record.reason,
                    'massive_controlled_assignment_id': record.id
                    })
            record.write({'state': '01_executed', })

    @api.multi
    def cancel_massive_controlled_assignment(self):
        for record in self:
            record.individualinput_ids.with_context(
                deleting_from_massive_controlled_assignment=True).unlink()
            record.write({'state': '00_draft', })

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        if (self.env.context and 'lang' in self.env.context):
            is_english = self.env.context['lang'] == 'en_US'
        else:
            is_english = True
        for record in self:
            superproduct_name = record.superproduct_id.name
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.event_time,
                    '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + superproduct_name
            if record.reason:
                name += ' - ' + record.reason
            result.append((record.id, name))
        return result

    @api.multi
    def action_show_individualinputs(self):
        self.ensure_one()
        if self.individualinput_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Individual Inputs'),
                'res_model': 'wua.individualinput',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.individualinput_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True}
                }
            return act_window

    @api.multi
    def action_select_parcels(self):
        self.ensure_one()
        if (not self.selected_parcels):
            self.populate_parcels_select()
            self.selected_parcels = True
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.massive.assignments.parcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'domain': [['massive_controlled_assignment_id', '=', self.id]],
            'limit': 10000000,
            }
        return act_window

    @api.multi
    def _compute_total_assignment_volume(self):
        for record in self:
            total_volume = 0
            for parcel in record.selected_assignment_parcel_ids:
                total_volume += parcel.assignment_provision_parcel
            record.total_assignment_volume = total_volume

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('quotaperiod_id', 'quotaperiod_id.is_closed')
    def _compute_closed_quotaperiod(self):
        for record in self:
            closed_quotaperiod = False
            if (record.quotaperiod_id and record.quotaperiod_id.is_closed):
                closed_quotaperiod = True
            record.closed_quotaperiod = closed_quotaperiod

    @api.depends('superproduct_id', 'superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            seq_number = self.env['ir.sequence'].next_by_code(
                'wua.massive.assignments')
            name = seq_number
            if record.superproduct_id and name:
                name += u'-' + str(
                    record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE)
            record.name = name

    @api.onchange('agriculturalseason_id')
    def _onchange_agriculturalseason_id(self):
        if self.agriculturalseason_id:
            return {
                'domain': {'quotaperiod_id':
                           [('agriculturalseason_id', '=',
                             self.agriculturalseason_id.id),
                            ('state', '=', 'generated')]}
                }

    @api.onchange('quotaperiod_id')
    def _onchange_quotaperiod_id(self):
        if self.quotaperiod_id:
            valid_superproduct_ids = []
            for quotaperiodline in self.quotaperiod_id.quotaperiodline_ids:
                valid_superproduct_ids.append(
                    quotaperiodline.superproduct_id.id)
            if valid_superproduct_ids:
                return {
                    'domain': {'superproduct_id':
                               [('id', 'in', valid_superproduct_ids)]}
                    }

    @api.onchange('superproduct_id')
    def _onchange_superproduct_id(self):
        if self.superproduct_id:
            default_categ = self.env['wua.individualinput.category'].search(
                [('superproduct_id', '=', self.superproduct_id.id)])
            if (default_categ and len(default_categ) > 0):
                self.category_id = default_categ[0]

    @api.onchange('provision')
    def _onchange_provision(self):
        parcels = self.env['wua.massive.assignments.parcel'].search(
            [('massive_controlled_assignment_id', '=', self._origin.id)])
        vals = {'provision': self.provision, }
        for parcel in parcels:
            parcel.write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaMassiveAssignments, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_provision = ' (m3/' + area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='provision']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.provision.string)
                node.set('string', original_label + suffix_provision)
            res['arch'] = etree.tostring(doc)
        return res

    @api.constrains('quotaperiod_id')
    def _check_quotaperiod_id(self):
        if len(self) == 1:
            if self.quotaperiod_id.state != 'generated':
                raise exceptions.UserError(
                    _('The state of quota period must be \'generated\'.'))
            if (self.agriculturalseason_id !=
               self.quotaperiod_id.agriculturalseason_id):
                raise exceptions.UserError(
                    _('The quota period is not within the chosen '
                      'agricultural season.'))

    @api.constrains('superproduct_id')
    def _check_superproduct_id(self):
        if len(self) == 1:
            if self.quotaperiod_id and self.quotaperiod_id.quotaperiodline_ids:
                ids_of_possible_superproducts = []
                for quotaperiodline in self.quotaperiod_id.quotaperiodline_ids:
                    ids_of_possible_superproducts.append(
                        quotaperiodline.superproduct_id.id)
                if (self.superproduct_id.id not in
                   ids_of_possible_superproducts):
                    raise exceptions.UserError(
                        _('The superproduct is not enrolled in the chosen '
                          'quota period.'))

    @api.constrains('event_time')
    def _check_event_time(self):
        if len(self) == 1:
            if self.quotaperiod_id:
                min_date = datetime.datetime.strptime(
                    self.quotaperiod_id.initial_date, '%Y-%m-%d')
                max_date = datetime.datetime.strptime(
                    self.quotaperiod_id.end_date, '%Y-%m-%d') + \
                    datetime.timedelta(days=1)
                event_time = datetime.datetime.strptime(
                    self.event_time, '%Y-%m-%d %H:%M:%S')
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(event_time)
                    event_time = event_time + offset
                if (event_time < min_date or event_time >= max_date):
                    raise exceptions.UserError(
                        _('The instant of this input is not within the '
                          'chosen quota period.'))

    def populate_parcels_select(self):
        parcels = self.env['wua.parcel'].search(
            [('active', '=', True),
             ('mapped_to_current_quotaperiod', '=', True)])
        if len(parcels) > 0:
            user_id = self.env.user.id
            massive_controlled_assignment_id = self.id
            provision = self.provision
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                  INSERT INTO wua_massive_assignments_parcel (
                    id, create_uid, write_uid, create_date, write_date,
                    massive_controlled_assignment_id, selected, parcel_id,
                    partner_id, area_official, provision)
                  SELECT nextval('wua_massive_assignments_parcel_id_seq'),
                    %s, %s, now(), now(), %s, TRUE, p.id, p.partner_id,
                  p.area_official, %s
                  FROM wua_parcel p
                  WHERE p.active AND p.mapped_to_current_quotaperiod
                        AND p.partner_id IS NOT NULL;""",
                                    (user_id, user_id,
                                     massive_controlled_assignment_id,
                                     provision))
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def _check_data(self, quotaperiod):
        data_ok = True
        error_message = ''
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        event_time = datetime.datetime.strptime(
            self.event_time, '%Y-%m-%d %H:%M:%S')
        if self.env.user.tz:
            local_timezone = pytz.timezone(self.env.user.tz)
            offset = local_timezone.utcoffset(event_time)
            event_time = event_time + offset
        if event_time < min_date or event_time >= max_date:
            data_ok = False
            error_message = _('The chosen date/time is outside the '
                              'quota period.')
        return data_ok, error_message

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp


class WuaMassiveAssignmentsParcel(models.Model):
    _name = 'wua.massive.assignments.parcel'
    _description = 'Parcel of Massive Assignment'
    _order = 'massive_controlled_assignment_id,parcel_id'

    massive_controlled_assignment_id = fields.Many2one(
        string='Assignment',
        comodel_name='wua.massive.assignments',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string='Selected',
        default=True)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        ondelete='restrict')

    concession_ids = fields.Many2many(
        string='Concessions',
        comodel_name='wua.concession',
        related='parcel_id.concession_ids',)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4))

    provision = fields.Float(
        string='Provision',
        digits=(32, 2))

    assignment_provision_parcel = fields.Float(
        string='Assignment Provision Parcel (m³)',
        digits=(32, 2),
        compute='_compute_assignment_provision_parcel')

    @api.multi
    def toggle_selected(self):
        for record in self:
            if record.selected:
                record.selected = False
            else:
                record.selected = True

    @api.multi
    def add_to_massive_assignment(self):
        vals = {'selected': True, }
        self.write(vals)

    @api.multi
    def remove_from_massive_assignment(self):
        vals = {'selected': False, }
        self.write(vals)

    @api.depends('area_official', 'provision')
    def _compute_assignment_provision_parcel(self):
        for record in self:
            record.assignment_provision_parcel = \
                record.area_official * record.provision

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaMassiveAssignmentsParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.area_official.string)
                area_measurement_name = ' (' + area_measurement_name + ')'
                node.set('string',  original_label + area_measurement_name)
            res['arch'] = etree.tostring(doc)
        return res

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp
