# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
import base64
from odoo import models, fields, api, modules, exceptions, _


class WuaAgendaitem(models.Model):
    _name = 'wua.agendaitem'
    _description = 'Agenda Item of an assembly'
    _inherit = 'mail.thread'
    _order = 'name'

    SIZE_ASSEMBLYCODE = 19
    SIZE_NUMERICSUFFIX = 4

    def _default_number(self):
        resp = 1
        current_assembly_id = \
            self.env.context.get('default_assembly_id', False)
        if current_assembly_id:
            agendaitems = self.env['wua.agendaitem'].search(
                [('assembly_id', '=', current_assembly_id)],
                limit=1, order='number desc')
            if agendaitems:
                resp = agendaitems[0].number + 1
        return resp

    def _default_assembly_state(self):
        resp = '01_draft'
        current_assembly_id = \
            self.env.context.get('default_assembly_id', False)
        if current_assembly_id:
            current_assembly = \
                self.env['wua.assembly'].browse(current_assembly_id)
            if current_assembly:
                resp = current_assembly.state
        return resp

    assembly_id = fields.Many2one(
        string='Assembly',
        comodel_name='wua.assembly',
        index=True,
        required=True,
        ondelete='cascade',)

    number = fields.Integer(
        string='Item Number',
        default=_default_number,
        required=True,)

    name = fields.Char(
        string='Agenda Item Identifier',
        size=SIZE_ASSEMBLYCODE + SIZE_NUMERICSUFFIX + 1,
        store=True,
        index=True,
        compute='_compute_name',)

    description = fields.Char(
        string='Agenda Item',
        required=True,
        track_visibility='onchange',)

    type_01_not_voteable = fields.Boolean(
        string='Type: Not voteable',
        default=False,)

    type_02_yes_or_no = fields.Boolean(
        string='Type: Yes/No',
        default=True,)

    type_03_options = fields.Boolean(
        string='Type: Multiple options',
        default=False,)

    type = fields.Selection(
        selection=[
            ('01_not_voteable', 'Not voteable'),
            ('02_yes_or_no', 'Yes/No'),
            ('03_options', 'Multiple options'),
        ],
        string='Type of agenda item',
        store=True,
        compute='_compute_type',
        default='02_yes_or_no',)

    count_yes = fields.Integer(
        string='Affirmative votes',
        default=0,
        required=True,)

    count_no = fields.Integer(
        string='Negative votes',
        default=0,
        required=True,)

    count_abstention = fields.Integer(
        string='Abstentions',
        default=0,
        required=True,)

    count_null = fields.Integer(
        string='Null votes',
        default=0,
        required=True,)

    count_total = fields.Integer(
        string='Total votes',
        compute='_compute_count_total',)

    approved = fields.Selection(
        selection=[
            ('01_yes', 'Yes'),
            ('02_no', 'No'),
            ('03_not_applicable', '-'),
        ],
        string='Approved Item',
        default='02_no',
        store=True,
        compute='_compute_approved',)

    icon_approved = fields.Binary(
        string='Icon for voting result',
        compute='_compute_icon_approved')

    assembly_state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='Assembly State',
        default=_default_assembly_state,
        store=True,
        compute='_compute_assembly_state',)

    option_ids = fields.One2many(
        string='Options',
        comodel_name='wua.agendaitem.option',
        inverse_name='agendaitem_id',)

    option_ids_readonly = fields.One2many(
        string='Options (read only)',
        comodel_name='wua.agendaitem.option',
        inverse_name='agendaitem_id',
        compute='_compute_option_ids_readonly',)

    chosen_option_id = fields.Many2one(
        string='Chosen Option (id)',
        comodel_name='wua.agendaitem.option',
        store=True,
        compute='_compute_chosen_option_id',)

    chosen_option = fields.Char(
        string='Chosen Option',
        compute='_compute_chosen_option',)

    internal_notes = fields.Html(
        string='Internal Notes',)

    final_summary = fields.Html(
        string='Final Summary',)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar agenda item.'),
        ('valid_count_yes', 'CHECK (count_yes >= 0)',
         'The number of votes in favor must be a value greater than or '
         'equal to 0.'),
        ('valid_count_no', 'CHECK (count_no >= 0)',
         'The number of votes against must be a value greater than or '
         'equal to 0.'),
        ('valid_count_abstention', 'CHECK (count_abstention >= 0)',
         'The number of abstentions must be a value greater than or '
         'equal to 0.'),
        ('valid_count_null', 'CHECK (count_null >= 0)',
         'The number of null votes must be a value greater than or '
         'equal to 0.'),
        ]

    @api.depends('assembly_id', 'assembly_id.name', 'number')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.assembly_id and record.assembly_id.name and
               record.number):
                name = record.assembly_id.name + '-' + \
                    str(record.number).zfill(self.SIZE_NUMERICSUFFIX)
            record.name = name

    @api.depends('type_01_not_voteable', 'type_02_yes_or_no',
                 'type_03_options')
    def _compute_type(self):
        for record in self:
            value_of_type = '02_yes_or_no'
            if record.type_01_not_voteable:
                value_of_type = '01_not_voteable'
            if record.type_03_options:
                value_of_type = '03_options'
            record.type = value_of_type

    @api.multi
    def _compute_count_total(self):
        for record in self:
            count_total = 0
            if record.type == '02_yes_or_no':
                count_total = record.count_yes + record.count_no + \
                    record.count_abstention + record.count_null
            if record.type == '03_options':
                for option in (record.option_ids or []):
                    count_total = count_total + option.count_option
            record.count_total = count_total

    @api.depends('type', 'count_yes', 'count_no')
    def _compute_approved(self):
        for record in self:
            approved = '03_not_applicable'
            if record.type == '02_yes_or_no':
                if record.count_yes > record.count_no:
                    approved = '01_yes'
                else:
                    approved = '02_no'
            record.approved = approved

    @api.multi
    def _compute_icon_approved(self):
        image_path_approved_yes = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_yes.png')
        image_path_approved_no = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_no.png')
        for record in self:
            icon_approved = None
            image_path = None
            if (record.assembly_state == '03_in_progress' or
               record.assembly_state == '04_finished'):
                if record.approved == '01_yes':
                    image_path = image_path_approved_yes
                if record.approved == '02_no':
                    image_path = image_path_approved_no
            if image_path:
                image_file = open(image_path, 'rb')
                icon_approved = base64.b64encode(image_file.read())
            record.icon_approved = icon_approved

    @api.depends('assembly_id', 'assembly_id.state')
    def _compute_assembly_state(self):
        for record in self:
            assembly_state = '01_draft'
            if record.assembly_id and record.assembly_id.state:
                assembly_state = record.assembly_id.state
            record.assembly_state = assembly_state

    @api.multi
    def _compute_option_ids_readonly(self):
        for record in self:
            option_ids_readonly = None
            if record.option_ids:
                option_ids_readonly = record.option_ids
            record.option_ids_readonly = option_ids_readonly

    @api.depends('option_ids', 'option_ids.count_option')
    def _compute_chosen_option_id(self):
        for record in self:
            chosen_option_id = None
            if record.option_ids:
                max_count_option = 0
                for option in record.option_ids:
                    if option.count_option > max_count_option:
                        chosen_option_id = option.id
                        max_count_option = option.count_option
            record.chosen_option_id = chosen_option_id

    @api.multi
    def _compute_chosen_option(self):
        for record in self:
            chosen_option = ''
            if record.chosen_option_id:
                chosen_option = record.chosen_option_id.option
            record.chosen_option = chosen_option

    @api.constrains('type_01_not_voteable', 'type_02_yes_or_no',
                    'type_03_options')
    def _check_type(self):
        for record in self:
            if ((record.type_01_not_voteable and
               record.type_02_yes_or_no) or
               (record.type_01_not_voteable and
               record.type_03_options) or
               (record.type_02_yes_or_no and
               record.type_03_options)):
                raise exceptions.UserError(
                    _('It is not possible to choose multiple types of voting.'))
            if ((not record.type_01_not_voteable) and
               (not record.type_02_yes_or_no) and
               (not record.type_03_options)):
                raise exceptions.UserError(
                    _('It is mandatory to choose a type of voting.'))
            if ((record.type_01_not_voteable or record.type_02_yes_or_no) and
               record.option_ids):
                raise exceptions.UserError(
                    _('An item of this type cannot have any options.'))

    @api.constrains('option_ids', 'type')
    def _check_type_and_options(self):
        for record in self:
            if (not record.option_ids) and record.type == '03_options':
                raise exceptions.UserError(
                    _('Some options are required.'))

    @api.onchange('type_01_not_voteable')
    def _onchange_type_01_not_voteable(self):
        if self.type_01_not_voteable:
            if self.type_02_yes_or_no:
                self.type_02_yes_or_no = False
            if self.type_03_options:
                self.type_03_options = False

    @api.onchange('type_02_yes_or_no')
    def _onchange_type_02_yes_or_no(self):
        if self.type_02_yes_or_no:
            if self.type_01_not_voteable:
                self.type_01_not_voteable = False
            if self.type_03_options:
                self.type_03_options = False

    @api.onchange('type_03_options')
    def _onchange_type_03_options(self):
        if self.type_03_options:
            if self.type_01_not_voteable:
                self.type_01_not_voteable = False
            if self.type_02_yes_or_no:
                self.type_02_yes_or_no = False

    @api.model
    def create(self, vals):
        vals = self._refine_vals(vals)
        return super(WuaAgendaitem, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            vals = self._refine_vals(vals)
        super(WuaAgendaitem, self).write(vals)
        return True

    def _refine_vals(self, vals):
        type_02_yes_or_no = self.type_02_yes_or_no
        if 'type_02_yes_or_no' in vals:
            type_02_yes_or_no = vals['type_02_yes_or_no']
        if not type_02_yes_or_no:
            vals['count_yes'] = 0
            vals['count_no'] = 0
            vals['count_abstention'] = 0
            vals['count_null'] = 0
        type_03_options = self.type_03_options
        if 'type_03_options' in vals:
            type_03_options = vals['type_03_options']
        if not type_03_options:
            vals['option_ids'] = [(5, 0, 0)]
        return vals

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = ('lang' in self.env.context and
                      self.env.context['lang'] == 'en_US')
        for record in self:
            name = ''
            if record.assembly_id and record.number:
                try:
                    if is_english:
                        locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                    assembly_date_str = datetime.datetime.strptime(
                        record.assembly_id.assembly_date,
                        '%Y-%m-%d').strftime('%x')
                finally:
                    locale.setlocale(locale.LC_TIME, default_locale)
                name = assembly_date_str + ' (' + \
                    record.assembly_id.issue + '), ' + \
                    _('item') + ' ' + str(record.number)
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        for record in self:
            if record.assembly_state != '01_draft':
                raise exceptions.UserError(_('It is only allowed to delete '
                                             'an agenda item '
                                             'in \'DRAFT\' state.'))
        super(WuaAgendaitem, self).unlink()


class WuaAgendaitemOption(models.Model):
    _name = 'wua.agendaitem.option'
    _description = 'Option of an agenda item'
    _order = 'name'

    SIZE_OPTION = 150

    agendaitem_id = fields.Many2one(
        string='Agenda Item',
        comodel_name='wua.agendaitem',
        index=True,
        required=True,
        ondelete='cascade',)

    sequence = fields.Integer(
        string='Display order',)

    option = fields.Char(
        string='Option',
        size=SIZE_OPTION,
        required=True,)

    name = fields.Char(
        string='Option Identifier',
        size=WuaAgendaitem.SIZE_ASSEMBLYCODE +
        WuaAgendaitem.SIZE_NUMERICSUFFIX + SIZE_OPTION + 2,
        store=True,
        compute='_compute_name',
        index=True,)

    count_option = fields.Integer(
        string='Votes',
        default=0,
        required=True,)

    assembly_state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='Assembly State',
        related='agendaitem_id.assembly_state',)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar option.'),
        ('valid_count_yes', 'CHECK (count_option >= 0)',
         'The number of votes of an option must be a value greater than or '
         'equal to 0.'),
        ]

    @api.depends('agendaitem_id', 'agendaitem_id.name', 'option')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.agendaitem_id and record.agendaitem_id.name and
               record.option):
                name = record.agendaitem_id.name + '-' + record.option
            record.name = name
