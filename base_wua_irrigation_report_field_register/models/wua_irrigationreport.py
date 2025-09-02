# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from lxml import etree
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
        domain="[('can_register_irrigationreport', '=', True)]",
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

    waterconnection_id = fields.Many2one(
        string="Waterconnection",
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_waterconnection_id',
    )

    waterconnection_with_watermeter = fields.Boolean(
        string="Waterconnection with watermeter",
        compute='_compute_waterconnection_with_watermeter',
        store=True,
        index=True,
    )

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

    @api.depends('irrigationshed_id')
    def _compute_waterconnection_id(self):
        for record in self:
            waterconnection_id = None
            if (record.irrigationshed_id):
                waterconnection_id = \
                    record.irrigationshed_id.waterconnection_ids[0]
            record.waterconnection_id = waterconnection_id

    @api.onchange('irrigationshed_id')
    @api.depends('waterconnection_id', 'waterconnection_id.watermeter_id')
    def _compute_waterconnection_with_watermeter(self):
        # If not manage WC, always return False
        manage_wc = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'manage_waterconnection_on_irrigationreports')
        for record in self:
            waterconnection_with_watermeter = False
            if (manage_wc and record.waterconnection_id and
                    record.waterconnection_id.watermeter_id):
                waterconnection_with_watermeter = True
            record.waterconnection_with_watermeter = \
                waterconnection_with_watermeter

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
            # If data in hours but don't watermeter management, check
            # hours * flow
            if data_in_hours and not record.waterconnection_with_watermeter:
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
            # If not data in hours or irrigationreport has a watermeter
            # check end_volume - initial_volume
            else:
                volume = record.end_volume - record.initial_volume
            if volume < 0:
                volume = 0
            record.volume = volume

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
        # CHeck if irrigationreport have parcel id associated
        parcel_id = -1
        parcel_name = ''
        if (irrigationreport.parcel_id):
            parcel_id = irrigationreport.parcel_id.id
            parcel_name = irrigationreport.parcel_id.name
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
            'parcel': parcel_id,
            'parcel_name': parcel_name,
            'partner_signature': partner_signature,
            'intake': irrigationreport.intake_id.id,
            'intake_name': irrigationreport.intake_id.name,
            'watering_element_type': watering_element_type,
            'watering_element': watering_element.id,
            'watering_element_name': watering_element.name,
            'volume': irrigationreport.volume,
            'adjustement_volume': irrigationreport.adjustement_volume,
            'volume_real': irrigationreport.volume_real,
            'init_time': epoch_init_time,
            'end_time': epoch_end_time,
            'report_initial_volume': irrigationreport.initial_volume,
            'report_end_volume': irrigationreport.end_volume,
            'hours': irrigationreport.hours,
            'state': irrigationreport.state,
            'conversion_factor': irrigationreport.conversion_factor,
            'volume_time_equivalence':
                irrigationreport.volume_time_equivalence,
            'volume_time_equivalence_ls':
                irrigationreport.volume_time_equivalence_ls,
            'sended': True,
            'notes':  irrigationreport.notes,
            'irrigationreport_img': irrigationreport_img,
            'credit_overdue': float(
                irrigationreport.partner_id.credit_overdue),
        }

    @api.model
    def create_field_irrigationreport(self, data):
        vals = {}
        # Get the real type from
        vals[self._possible_types_id[data['watering_element_type']]] = \
            data['watering_element_id']
        vals['irrigationreport_writer_id'] = data['irrigationreport_writer_id']
        vals['user_id'] = data['irrigationreport_writer_id']
        vals['partner_id'] = data['partner_id']
        if (data['parcel_id'] > 0):
            vals['parcel_id'] = data['parcel_id']
        # Initial date and end date must be on epoch format
        initial_date_formatted = datetime.datetime.fromtimestamp(
            data['initial_date'], pytz.utc)
        initial_date_str = initial_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
        end_date_formatted = datetime.datetime.fromtimestamp(
            data['end_date'], pytz.utc)
        end_date_str = end_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
        vals['report_initial_time'] = initial_date_str
        vals['report_end_time'] = end_date_str
        # use max, because initial_volume can get a -1 if not setted
        vals['initial_volume'] = max(data['report_initial_volume'], 0)
        # use max, because end_volume can get a -1 if not setted
        vals['end_volume'] = max(data['report_end_volume'], 0)
        vals['conversion_factor'] = data['conversion_factor']
        vals['volume_time_equivalence'] = data['volume_time_equivalence']
        vals['volume_time_equivalence_ls'] = data['volume_time_equivalence_ls']
        difference_time = end_date_formatted - initial_date_formatted
        # 3600.0 To getting a float result of hours
        vals['hours'] = difference_time.days * 24 + \
            difference_time.seconds / 3600.0
        vals['notes'] = data['notes']
        if (data['partner_signature']):
            vals['partner_signature'] = data['partner_signature']
        if (data['irrigationreport_img']):
            vals['irrigationreport_img'] = data['irrigationreport_img']
        has_default_intake = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'has_default_field_irrigationreport_intake_id')
        if (has_default_intake):
            vals['intake_id'] = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'default_field_irrigationreport_intake_id')
        else:
            vals['intake_id'] = data['intake_id']
        # Get default water from the default intake water
        intake_obj = self.env['wua.intake'].browse(vals['intake_id'])
        vals['product_id'] = intake_obj.product_id.id
        # Creation of new value
        new_irrigationreport = self.env['wua.irrigationreport'].create(vals)
        # If succesfull creation return the id, and volumnes
        return self.format_irrigationreport(new_irrigationreport)

    @api.model
    def update_field_irrigationreport(self, data):
        vals = {}
        irrigationreport = self.env['wua.irrigationreport'].browse(
            data['irrigationreport_id'])
        vals['notes'] = data['notes']
        if (data['partner_signature']):
            vals['partner_signature'] = data['partner_signature']
        if (data['irrigationreport_img']):
            vals['irrigationreport_img'] = data['irrigationreport_img']
        if (irrigationreport.state == 'draft'):
            vals['hours'] = data['hours']
            vals['conversion_factor'] = data['conversion_factor']
            # use max, because initial_volume can get a -1 if not setted
            vals['initial_volume'] = max(data['report_initial_volume'], 0)
            # use max, because end_volume can get a -1 if not setted
            vals['end_volume'] = max(data['report_end_volume'], 0)
            vals['volume_time_equivalence'] = data['volume_time_equivalence']
            vals['volume_time_equivalence_ls'] = data[
                'volume_time_equivalence_ls']
            end_date_formatted = datetime.datetime.fromtimestamp(
                data['end_date'], pytz.utc)
            end_date_str = end_date_formatted.strftime('%Y-%m-%d %H:%M:%S')
            vals['report_end_time'] = end_date_str
            has_default_intake = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'has_default_field_irrigationreport_intake_id')
            if (not has_default_intake):
                vals['intake_id'] = data['intake_id']
                # Get default water from the default intake water
                intake_obj = self.env['wua.intake'].browse(vals['intake_id'])
                vals['product_id'] = intake_obj.product_id.id
        irrigationreport.write(vals)
        return self.format_irrigationreport(irrigationreport)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationReport, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        manage_waterconnection_on_irrigationreports = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'manage_waterconnection_on_irrigationreports')
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if data_in_hours and manage_waterconnection_on_irrigationreports:
                for node in doc.xpath("//field[@name='initial_volume']"):
                    if ('invisible' in node.attrib):
                        node.attrib.pop('invisible')
                    node.set('modifiers',
                             '{"invisible": '
                             '[["waterconnection_with_watermeter", "=",'
                             'false]],'
                             '"readonly": '
                             '[["invoiced", "=",'
                             'true]],'
                             '"required": true}')
                for node in doc.xpath("//field[@name='end_volume']"):
                    if ('invisible' in node.attrib):
                        node.attrib.pop('invisible')
                    node.set('modifiers',
                             '{"invisible": '
                             '[["waterconnection_with_watermeter", "=",'
                             'false]],'
                             '"readonly": '
                             '[["invoiced", "=",'
                             'true]],'
                             '"required": true}')
            res['arch'] = etree.tostring(doc)
        return res
