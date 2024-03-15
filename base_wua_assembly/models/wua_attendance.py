# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import locale
from lxml import etree
from datetime import datetime
from odoo import models, fields, api, modules, _


class WuaAttendance(models.Model):
    _name = 'wua.attendance'
    _description = 'Attendance of a partner to an assembly'
    _order = 'assembly_id, participant_name'

    SIZE_ASSEMBLY_NAME = 19
    SIZE_PARTNER_CODE = 6

    assembly_id = fields.Many2one(
        string='Assembly',
        comodel_name='wua.assembly',
        index=True,
        required=True,
        ondelete='cascade',)

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        domain=[('is_wua_partner', '=', True)],
        index=True,
        required=True,
        ondelete='restrict',)

    name = fields.Char(
        string='Attendance Identifier',
        size=SIZE_ASSEMBLY_NAME + SIZE_PARTNER_CODE + 1,
        store=True,
        index=True,
        compute='_compute_name',)

    votes_owned = fields.Integer(
        string='Own Votes',
        default=0,
        required=True,)

    votes_delegation = fields.Integer(
        string='Votes by delegation',
        default=0,
        required=True,)

    votes_total = fields.Integer(
        string='Total Votes',
        store=True,
        index=True,
        compute='_compute_votes_total',)

    participant_id = fields.Many2one(
        string='Participant',
        comodel_name='res.partner',
        index=True,
        store=True,
        compute='_compute_participant_id',)

    participant_name = fields.Char(
        string='Participant Name',
        index=True,
        store=True,
        compute='_compute_participant_name',)

    vat_participant = fields.Char(
        string='TIN (participant)',
        index=True,
        store=True,
        compute='_compute_vat_participant',)

    vat_partner = fields.Char(
        string='TIN of partner',
        index=True,
        store=True,
        compute='_compute_vat_partner',)

    represented_partner = fields.Char(
        string='Represented Partner',
        compute='_compute_represented_partner',)

    assembly_state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='Assembly State',
        default='02_called',
        store=True,
        compute='_compute_assembly_state',)

    receiver_id = fields.Many2one(
        string='Receiver (if there is voting delegation)',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',)

    potential_attendee = fields.Boolean(
        string='Potential Attendee (y/n)',
        store=True,
        compute='_compute_potential_attendee',)

    present = fields.Boolean(
        string='Present',
        default=False,)

    attendance_signature = fields.Binary(
        string='Signature')

    icon_present = fields.Binary(
        string='Icon for the attendance',
        compute='_compute_icon_present')

    participant_image = fields.Binary(
        string='Participant Image',
        compute='_compute_participant_image')

    html_attendance_title = fields.Html(
        string='Attendance Title',
        compute='_compute_html_attendance_title')

    assignors = fields.Html(
        string='Assignors',
        compute='_compute_assignors')

    compressed_assignors = fields.Html(
        string='Assignors (compressed)',
        compute='_compute_compressed_assignors')

    attendance_notes = fields.Text(
        string='Attendance Notes')

    param_allow_notes_in_signature = fields.Boolean(
        string='Allow notes with the partner signature',
        compute='_compute_param_allow_notes_in_signature')

    with_attendance_notes = fields.Boolean(
        string='There are notes (y/n)',
        default=False,
        readonly="1")

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar attendance record.'),
        ('valid_votes_owned', 'CHECK (votes_owned >= 0)',
         'The number of own votes must be a value greater than or '
         'equal to 0.'),
        ]

    @api.depends('assembly_id', 'assembly_id.name',
                 'partner_id', 'partner_id.partner_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.assembly_id and record.assembly_id.name and
               record.partner_id and record.partner_id.partner_code):
                name = record.assembly_id.name + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.SIZE_PARTNER_CODE)
            record.name = name

    @api.depends('votes_owned', 'votes_delegation')
    def _compute_votes_total(self):
        for record in self:
            record.votes_total = record.votes_owned + record.votes_delegation

    @api.depends('partner_id')
    def _compute_participant_id(self):
        for record in self:
            participant_id = record.partner_id
            agent_id = self._get_agent_of_participant(
                record.assembly_id, record.partner_id)
            if agent_id or record.partner_id.legalrep_id:
                if agent_id:
                    participant_id = agent_id.id
                else:
                    participant_id = record.partner_id.legalrep_id
            record.participant_id = participant_id

    @api.depends('participant_id')
    def _compute_participant_name(self):
        for record in self:
            participant_name = ''
            if record.participant_id:
                participant_name = record.participant_id.name
            record.participant_name = participant_name

    @api.depends('participant_id')
    def _compute_vat_participant(self):
        for record in self:
            vat_participant = ''
            if record.participant_id:
                if record.participant_id.is_wua_partner:
                    vat_participant = record.participant_id.vat
                else:
                    vat_participant = record.participant_id.vat_wua_legalrep
            record.vat_participant = vat_participant

    @api.depends('partner_id')
    def _compute_vat_partner(self):
        for record in self:
            vat_partner = ''
            if record.partner_id and record.partner_id.vat:
                vat_partner = record.partner_id.vat
            record.vat_partner = vat_partner

    @api.multi
    def _compute_represented_partner(self):
        for record in self:
            represented_partner = ''
            if record.participant_name != record.partner_id.name:
                represented_partner = record.partner_id.name
            record.represented_partner = represented_partner

    @api.depends('assembly_id', 'assembly_id.state')
    def _compute_assembly_state(self):
        for record in self:
            assembly_state = '01_draft'
            if record.assembly_id and record.assembly_id.state:
                assembly_state = record.assembly_id.state
            record.assembly_state = assembly_state

    @api.depends('receiver_id')
    def _compute_potential_attendee(self):
        for record in self:
            potential_attendee = True
            if record.receiver_id:
                potential_attendee = False
            record.potential_attendee = potential_attendee

    @api.multi
    def _compute_icon_present(self):
        image_path_present_yes = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_yes.png')
        image_path_present_no = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_no.png')
        for record in self:
            icon_present = None
            image_path = None
            if record.present:
                image_path = image_path_present_yes
            else:
                image_path = image_path_present_no
            if image_path:
                image_file = open(image_path, 'rb')
                icon_present = base64.b64encode(image_file.read())
            record.icon_present = icon_present

    @api.multi
    def _compute_participant_image(self):
        for record in self:
            participant_image = None
            if record.participant_id:
                participant_image = record.participant_id.image_medium
            record.participant_image = participant_image

    @api.multi
    def _compute_html_attendance_title(self):
        try:
            settings = self.env['res.backend.settings'].search([])
            report_color = str(settings[0].report_motive_color)
        except Exception:
            report_color = '#696969'
        for record in self:
            html_attendance_title = ''
            if record.name:
                label_title = _('VOTES')
                header = '<div class="text-center" ' + \
                         'style="margin-top:8px"><b>' + label_title + \
                         '</b></div>'
                body = '<div class="text-center"><h1>' + \
                    str(record.votes_total) + '</h1></div>'
                html_attendance_title = \
                    '<div class="panel-body text-left" ' + \
                    'style="background:#f4f6f6;' + \
                    'border-color: ' + report_color + '; border-width:1px;' + \
                    'border-style:solid;padding-top:0px;' + \
                    'padding-bottom:0px;' + \
                    'margin-left:120px;margin-right:120px">' + \
                    header + body + '</div>'
            record.html_attendance_title = html_attendance_title

    @api.multi
    def _compute_assignors(self):
        model_wua_delegationvote = self.env['wua.delegationvote']
        for record in self:
            assignors = ''
            delegationvotes_of_attendance = \
                model_wua_delegationvote.search(
                    [('assembly_id', '=', record.assembly_id.id),
                     ('receiver_id', '=', record.partner_id.id),
                     ('state', '=', '02_validated')])
            if delegationvotes_of_attendance:
                raw_list = []
                for delegationvote in delegationvotes_of_attendance:
                    raw_list.append(
                        delegationvote.grantor_id.name + ' (' +
                        str(delegationvote.grantor_id.number_of_votes) + ')')
                sorted_list = sorted(raw_list)
                for item in sorted_list:
                    assignors = assignors + item + '<br/>'
                assignors = assignors[:-5]
            record.assignors = assignors

    @api.multi
    def _compute_param_allow_notes_in_signature(self):
        param_allow_notes_in_signature = True
        value_of_param_allow_notes_in_signature = \
            self.env['ir.values'].get_default(
                'wua.assembly.configuration', 'allow_notes_in_signature')
        if not value_of_param_allow_notes_in_signature:
            param_allow_notes_in_signature = False
        for record in self:
            record.param_allow_notes_in_signature = \
                param_allow_notes_in_signature

    @api.multi
    def _compute_compressed_assignors(self):
        model_wua_delegationvote = self.env['wua.delegationvote']
        for record in self:
            compressed_assignors = ''
            delegationvotes_of_attendance = \
                model_wua_delegationvote.search(
                    [('assembly_id', '=', record.assembly_id.id),
                     ('receiver_id', '=', record.partner_id.id),
                     ('state', '=', '02_validated')])
            if delegationvotes_of_attendance:
                raw_list = []
                for delegationvote in delegationvotes_of_attendance:
                    raw_list.append(
                        delegationvote.grantor_id.name + ' (' +
                        str(delegationvote.grantor_id.number_of_votes) + ')')
                sorted_list = sorted(raw_list)
                num_item = 0
                for item in sorted_list:
                    num_item = num_item + 1
                    if (num_item % 4) == 0:
                        compressed_assignors = \
                            compressed_assignors + item + ', <br/>'
                    else:
                        compressed_assignors = \
                            compressed_assignors + item + ', '
                if (num_item % 4) == 0:
                    compressed_assignors = compressed_assignors[:-7]
                else:
                    compressed_assignors = compressed_assignors[:-2]
            record.compressed_assignors = compressed_assignors

    @api.multi
    def write(self, vals):
        if 'attendance_signature' in vals:
            if vals['attendance_signature']:
                vals['present'] = True
            else:
                vals['present'] = False
        super(WuaAttendance, self).write(vals)
        return True

    @api.multi
    def name_get(self):
        result = []
        if self.env.context.get('show_only_participant', False):
            for record in self:
                result.append((record.id, record.participant_name))
        else:
            default_locale = locale.setlocale(locale.LC_TIME)
            if (self.env.context and 'lang' in self.env.context):
                is_english = self.env.context['lang'] == 'en_US'
            else:
                is_english = True
            for record in self:
                try:
                    if is_english:
                        locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                    assembly_date_str = datetime.strptime(
                        record.assembly_id.assembly_date,
                        '%Y-%m-%d').strftime('%x')
                finally:
                    locale.setlocale(locale.LC_TIME, default_locale)
                name = assembly_date_str + ' (' + record.participant_name + ')'
                result.append((record.id, name))
        return result

    def _get_agent_of_participant(self, assembly, partner):
        resp = None
        representation = self.env['wua.representation'].search(
            [('assembly_id', '=', assembly.id),
             ('partner_id', '=', partner.id),
             ('state', '=', '02_validated')])
        if representation:
            resp = representation[0].agent_id
        return resp

    @api.multi
    def confirm_present_value(self):
        self.ensure_one()
        return {'type': 'ir.actions.client', 'tag': 'history_back'}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaAttendance, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['toolbar']['print'] = []
        value_of_param_allow_notes_in_signature = \
            self.env['ir.values'].get_default(
                'wua.assembly.configuration', 'allow_notes_in_signature')
        if not value_of_param_allow_notes_in_signature:
            if view_type == 'tree':
                doc = etree.XML(res['arch'])
                for tree in doc.xpath('//tree'):
                    node_to_remove = None
                    for field in tree:
                        node_as_str = etree.tostring(field)
                        if node_as_str.find('name="attendance_notes"') != -1:
                            node_to_remove = field
                            break
                    if node_to_remove is not None:
                        tree.remove(node_to_remove)
                res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def action_activate_notes(self, attendance_id):
        if attendance_id:
            attendance = self.browse(attendance_id)
            if attendance:
                attendance.write({'with_attendance_notes': True, })
