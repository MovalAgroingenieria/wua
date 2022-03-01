# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    _possible_types_id = {
        'irrigationshed': 'irrigationshed_id',
        'flowdivider': 'flowdivider_id',
        'irrigationgate': 'irrigationgate_id',
    }

    irrigationshed_id = fields.Many2one(
        string="Irrigationshed",
        index=True,
        comodel_name="wua.irrigationshed",
        readonly=True,
        ondelete="restrict")

    irrigationgate_id = fields.Many2one(
        string="Irrigationgate",
        index=True,
        comodel_name="wua.irrigationgate",
        readonly=True,
        ondelete="restrict")

    flowdivider_id = fields.Many2one(
        string="Flowdivider",
        index=True,
        comodel_name="wua.flowdivider",
        readonly=True,
        ondelete="restrict")

    irrigationreport_writer_id = fields.Many2one(
        string="Irrigationreport Writer",
        index=True,
        comodel_name="res.users",
        ondelete='restrict',
        readonly=True)

    is_field_irrigationreport = fields.Boolean(
        string="Field Irrigationreport",
        compute='_compute_is_field_irrigationreport',
        store=True)

    with_end_time = fields.Boolean(
        string='End time entered by the irrigator',
        compute='_compute_with_end_time',
        store=True)

    irrigationreport_img = fields.Binary(
        string="Irrigationreport Image",
        readonly=True,
        attachment=True)

    @api.constrains('is_field_irrigationreport')
    def _check_is_field_irrigationreport(self):
        if (len(self) == 1 and (self.is_field_irrigationreport) and
                (not self.irrigationreport_writer_id)):
            raise exceptions.ValidationError(_(
                'Field irrigationreport must have an irrigationreport '
                'writer.'))

    @api.constrains('irrigationreport_writer_id')
    def _check_irrigationreport_writer_id(self):
        if (len(self) == 1 and (self.irrigationreport_writer_id) and
                (not self.irrigationreport_writer_id.has_group(
                    'base_wua_irrigation_report_field_register.'
                    'group_wua_irrigation_report_writer'))):
            raise exceptions.ValidationError(_(
                'This User don\'t belongs to irrigationreport writer group.'))

    @api.depends('irrigationreport_writer_id')
    def _compute_is_field_irrigationreport(self):
        for record in self:
            is_field_irrigationreport = False
            if (record.irrigationreport_writer_id):
                is_field_irrigationreport = True
            record.is_field_irrigationreport = is_field_irrigationreport

    @api.depends('is_field_irrigationreport', 'report_initial_time',
                 'report_end_time')
    def _compute_with_end_time(self):
        for record in self:
            with_end_time = True
            if (record.is_field_irrigationreport and
                    record.report_initial_time == record.report_end_time):
                with_end_time = False
            record.with_end_time = with_end_time

    # inherit method
    def validate_irrigationreport(self):
        self.ensure_one()
        if (not self.with_end_time):
            raise exceptions.ValidationError(_(
                'Could not validate, field irrigationreport don\'t have an '
                'end time.'))
        super(WuaIrrigationReport, self).validate_irrigationreport()

    # Overwrite method
    def validate_irrigationreports(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if (irrigationreport.state == 'draft' and
                    irrigationreport.with_end_time):
                irrigationreport.validate_irrigationreport()

    # Returns an object prepared to api response when an irrigationreport
    # is created or updated
    def format_irrigationreport(self, irrigationreport):
        # Get return object for javascript
        epoch_init_time = (datetime.datetime.strptime(
            irrigationreport.report_initial_time, '%Y-%m-%d %H:%M:%S') -
            datetime.datetime(1970, 1, 1)).total_seconds() * 1000
        epoch_end_time = False
        # Irrigationreport not closed
        if irrigationreport.with_end_time:
            epoch_end_time = (datetime.datetime.strptime(
                irrigationreport.report_end_time, '%Y-%m-%d %H:%M:%S') -
                datetime.datetime(1970, 1, 1)).total_seconds() * 1000
        partner_signature = irrigationreport.partner_signature
        # Format for dataURL
        if (partner_signature):
            partner_signature = 'data:image/png;base64,' + partner_signature
        else:
            partner_signature = ''
        irrigationreport_img = irrigationreport.irrigationreport_img
        if (irrigationreport_img):
            irrigationreport_img = 'data:image/png;base64,' + \
                irrigationreport_img
        else:
            irrigationreport_img = ''
        if (irrigationreport.irrigationshed_id):
            watering_element_type = 'irrigationshed'
            watering_element = irrigationreport.irrigationshed_id
        elif (irrigationreport.flowdivider_id):
            watering_element_type = 'flowdivider'
            watering_element = irrigationreport.flowdivider_id
        elif (irrigationreport.irrigationgate_id):
            watering_element_type = 'irrigationgate'
            watering_element = irrigationreport.irrigationgate_id
        return {
            'id': irrigationreport.id,
            'partner': irrigationreport.partner_id.id,
            'partner_name': irrigationreport.partner_id.name,
            'partner_signature': partner_signature,
            'watering_element_type': watering_element_type,
            'watering_element': watering_element.id,
            'watering_element_name': watering_element.name,
            'volume': irrigationreport.volume,
            'adjustement_volume': irrigationreport.adjustement_volume,
            'volume_real': irrigationreport.volume_real,
            'init_time': epoch_init_time,
            'end_time': epoch_end_time,
            'hours': irrigationreport.hours,
            'state': irrigationreport.state,
            'sended': True,
            'notes':  irrigationreport.notes,
            'irrigationreport_img': irrigationreport_img,
        }

    @api.model
    def create_field_irrigationreport(
            self, watering_element_type, watering_element_id,
            irrigationreport_writer_id,
            initial_date, end_date, partner_id, notes='',
            partner_signature='', irrigationreport_img=''):
        vals = {}
        # Get the real type from
        vals[self._possible_types_id[watering_element_type]] = \
            watering_element_id
        vals['irrigationreport_writer_id'] = irrigationreport_writer_id
        vals['user_id'] = irrigationreport_writer_id
        vals['partner_id'] = partner_id
        # Initial date and end date must be on epoch format
        initial_date_formatted = datetime.datetime.fromtimestamp(
            initial_date, pytz.utc)
        initial_date_str = initial_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
        end_date_formatted = datetime.datetime.fromtimestamp(
            end_date, pytz.utc)
        end_date_str = end_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
        vals['report_initial_time'] = initial_date_str
        vals['report_end_time'] = end_date_str
        difference_time = end_date_formatted - initial_date_formatted
        # 3600.0 To getting a float result of hours
        vals['hours'] = difference_time.days * 24 + \
            difference_time.seconds / 3600.0
        vals['notes'] = notes
        if (partner_signature):
            vals['partner_signature'] = partner_signature
        if (irrigationreport_img):
            vals['irrigationreport_img'] = irrigationreport_img
        vals['intake_id'] = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'default_field_irrigationreport_intake_id')
        # Creation of new value
        new_irrigationreport = self.env['wua.irrigationreport'].create(vals)
        # If succesfull creation return the id, and volumnes
        return self.format_irrigationreport(new_irrigationreport)

    @api.model
    def update_field_irrigationreport(
        self, irrigationreport_id, end_date, hours, notes, partner_signature,
            irrigationreport_img):
        vals = {}
        irrigationreport = self.env['wua.irrigationreport'].browse(
            irrigationreport_id)
        vals['notes'] = notes
        if (partner_signature):
            vals['partner_signature'] = partner_signature
        if (irrigationreport_img):
            vals['irrigationreport_img'] = irrigationreport_img
        if (irrigationreport.state == 'draft'):
            vals['hours'] = hours
            end_date_formatted = datetime.datetime.fromtimestamp(
                end_date, pytz.utc)
            end_date_str = end_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
            vals['report_end_time'] = end_date_str
        irrigationreport.write(vals)
        return self.format_irrigationreport(irrigationreport)
