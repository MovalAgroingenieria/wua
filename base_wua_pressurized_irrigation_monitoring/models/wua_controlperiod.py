# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
import os
import logging
import xlrd
from datetime import timedelta
from odoo import models, fields, api, _, exceptions, SUPERUSER_ID
from odoo.tools import config


class WuaControlperiod(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.controlperiod'
    _description = 'Entity (control period)'
    _order = 'name'

    # Size of fields "name" and "description".
    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 75

    name = fields.Char(
        string='Control Period',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated')
        ],
        default='draft',
        string='State',
    )

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True
    )

    end_date = fields.Date(
        string='End Date',
        default=lambda self: fields.datetime.now() + timedelta(days=7),
        required=True,
        index=True
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='cascade',
        required=True
    )

    et0_value = fields.Float(
        string='ET0 Value (mm)',
        digits=(32, 2),
        default=0)

    pe_value = fields.Float(
        string='Precipitation (mm)',
        digits=(32, 2),
        default=0)

    estimated_consumption = fields.Float(
        string='Estimated Consumption (m3)',
        digits=(32, 4),
        compute='_compute_estimated_consumption',
        store=True
    )

    real_consumption = fields.Float(
        string='Real Consumption (m3)',
        digits=(32, 4),
        compute='_compute_real_consumption',
        store=True
    )

    deviation = fields.Float(
        string='Deviation (m3)',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True
    )

    notes = fields.Html(
        string='Notes'
    )

    controlpresconsumption_ids = fields.One2many(
        string="Control Consumptions",
        comodel_name="wua.controlpresconsumption",
        inverse_name="controlperiod_id"
    )

    subparcel_presconsumption_ids = fields.One2many(
        string="Comparative Subparcel Presconsumption",
        comodel_name="wua.comparative.subparcel.presconsumption",
        inverse_name="controlperiod_id"
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ('valid_et0_value',
         'CHECK (et0_value >= 0)',
         'The ET0 must be a value zero or positive.'),
        ('valid_pe_value',
         'CHECK (pe_value >= 0)',
         'The precipitation must be a value zero or positive.'),
        ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.estimated_consumption')
    def _compute_estimated_consumption(self):
        for record in self:
            estimated_consumption = 0
            for subp_pres in record.subparcel_presconsumption_ids:
                estimated_consumption += subp_pres.estimated_consumption
            record.estimated_consumption = estimated_consumption

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.real_consumption')
    def _compute_real_consumption(self):
        for record in self:
            real_consumption = 0
            for subp_pres in record.subparcel_presconsumption_ids:
                real_consumption += subp_pres.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1 and
           ((self.initial_date < self.agriculturalseason_id.initial_date) or
           (self.end_date > self.agriculturalseason_id.end_date))):
            raise exceptions.ValidationError(_(
                'The control period limits are outside the agricultural '
                'season.'))

    @api.constrains('initial_date', 'end_date')
    def _check_others_controlperiods(self):
        controlperiods = self.env['wua.controlperiod'].search(
            ['&', ('initial_date', '<=', self.end_date),
             ('end_date', '>=', self.initial_date)])
        if (len(self) == 1 and len(controlperiods) > 1):
            raise exceptions.ValidationError(_(
                'The control period overlaps with another.'))

    @api.model
    def create(self, vals):
        new_controlperiod = super(WuaControlperiod, self).create(vals)
        ctrl_pres = self.env['wua.controlpresconsumption'].search(
            ['&', ('reading_end_time', '<=', new_controlperiod.end_date),
             ('reading_initial_time', '>=', new_controlperiod.initial_date)])
        if (len(ctrl_pres) > 0):
            ctrl_pres.write({
                'controlperiod_id': new_controlperiod.id
            })
        filtered_subparcels = self.env['wua.parcel.subparcel'].search(
            [('cultivation_id.monitoring', '=', True)])
        if len(filtered_subparcels) > 0:
            comp_subp_presc = \
                self.env['wua.comparative.subparcel.presconsumption']
            for subparcel in filtered_subparcels:
                comp_subp_presc.create({
                    'subparcel_id': subparcel.id,
                    'parcel_id': subparcel.parcel_id.id,
                    'cadastral_reference':
                        subparcel.parcel_id.cadastral_reference,
                    'area_perc': subparcel.area_perc,
                    'irrigationsystem_id': subparcel.irrigationsystem_id.id,
                    'tree_distance': subparcel.tree_distance,
                    'tree_development': subparcel.tree_development,
                    'tree_lateral_number': subparcel.tree_lateral_number,
                    'tree_drippers_number': subparcel.tree_drippers_number,
                    'row_distance': subparcel.row_distance,
                    'controlperiod_id': new_controlperiod.id,
                    'partner_id': subparcel.partner_id.id,
                    'hydraulicsector_id': subparcel.hydraulicsector_id.id,
                    'cultivation_id': subparcel.cultivation_id.id,
                    'cultivationvariety_id':
                        subparcel.cultivationvariety_id.id,
                    'area_official': subparcel.area_official,
                    'productionmethod_id': subparcel.productionmethod_id.id,
                    'shaded_percentage': subparcel.shaded_percentage,
                    'soil_type': subparcel.soil_type,
                    'organic_material_percentage':
                        subparcel.organic_material_percentage,
                    'orientation': subparcel.orientation,
                    'drippers_number': subparcel.drippers_number,
                    'drippers_nominal_flow': subparcel.drippers_nominal_flow,
                    'plantation_year': subparcel.plantation_year,
                    'cultivation_age': subparcel.cultivation_age,
                    'age_category': subparcel.age_category,
                    })
        return new_controlperiod

    @api.multi
    def write(self, vals):
        periods_to_calculate_ids = []
        super(WuaControlperiod, self).write(vals)
        if ('et0_value' in vals or 'pe_value' in vals):
            for record in self:
                periods_to_calculate_ids.append(record.id)
        if periods_to_calculate_ids:
            self.calculate_controlperiods(periods_to_calculate_ids)
        return True

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = False
        if 'lang' in self.env.context:
            is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def calculate_controlperiod(self):
        self.ensure_one()
        controlperiod = self
        self.regenerate_comparative_consumptions_of_controlperiod(
            controlperiod)
        controlperiod.state = 'calculated'
        controlperiod.message_post(
            _('Calculated control-period.') + ' ' +
            _('Estimated consumption:') + ' ' +
            '{:.2f}'.format(controlperiod.estimated_consumption) + ' m3. ' +
            _('Real consumption:') + ' ' +
            '{:.2f}'.format(controlperiod.real_consumption) + ' m3. ' +
            _('Deviation:') + ' ' +
            '{:.2f}'.format(controlperiod.deviation) + ' m3.')

    @api.multi
    def cancel_controlperiod(self):
        self.ensure_one()
        controlperiod = self
        if controlperiod.subparcel_presconsumption_ids:
            controlperiod.subparcel_presconsumption_ids.write(
                {'theoretical_consumption': 0,
                 'real_consumption': 0})
        controlperiod.state = 'draft'
        controlperiod.message_post(
            _('Cancelled control-period.'))

    def calculate_controlperiods(self, active_controlperiods):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        controlperiods = self.env['wua.controlperiod'].browse(
            active_controlperiods)
        for controlperiod in controlperiods:
            controlperiod.calculate_controlperiod()

    def cancel_controlperiods(self, active_controlperiods):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        controlperiods = self.env['wua.controlperiod'].browse(
            active_controlperiods)
        for controlperiod in controlperiods:
            controlperiod.cancel_controlperiod()

    def get_wua_controlperiod_comparative_presconsumption_action(self):
        current_controlperiod_id = self.env.context.get('active_id')
        condition = [('controlperiod_id', '=', current_controlperiod_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Subparcels'),
            'res_model': 'wua.comparative.subparcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            }
        return act_window

    def get_wua_controlperiod_control_presconsumption_action(self):
        current_controlperiod_id = self.env.context.get('active_id')
        condition = [('controlperiod_id', '=', current_controlperiod_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Control Consumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': self.env.context,
            }
        return act_window

    def regenerate_comparative_consumptions_of_controlperiod(self,
                                                             controlperiod):
        if not controlperiod.agriculturalseason_id.active_agriculturalseason:
            raise exceptions.UserError(_(
                'The agricultural season is not active.'))
        subparcels = self.env['wua.parcel.subparcel'].search(
            [('cultivation_id.monitoring', '=', True)])
        if not subparcels:
            raise exceptions.UserError(_(
                'There are no subparcels with monitored cultivations.'))
        comp_subp_pcons = controlperiod.subparcel_presconsumption_ids
        if comp_subp_pcons:
            comp_subp_pcons.unlink()
        comp_subp_pcons_model = \
            self.env['wua.comparative.subparcel.presconsumption']
        for subparcel in subparcels:
            comp_subp_pcons_model.create({
                'subparcel_id': subparcel.id,
                'parcel_id': subparcel.parcel_id.id,
                'cadastral_reference': subparcel.parcel_id.cadastral_reference,
                'area_perc': subparcel.area_perc,
                'irrigationsystem_id': subparcel.irrigationsystem_id.id,
                'tree_distance': subparcel.tree_distance,
                'tree_drippers_number': subparcel.tree_drippers_number,
                'tree_development': subparcel.tree_development,
                'tree_lateral_number': subparcel.tree_lateral_number,
                'row_distance': subparcel.row_distance,
                'controlperiod_id': controlperiod.id,
                'partner_id': subparcel.partner_id.id,
                'hydraulicsector_id': subparcel.hydraulicsector_id.id,
                'cultivation_id': subparcel.cultivation_id.id,
                'cultivationvariety_id': subparcel.cultivationvariety_id.id,
                'area_official': subparcel.area_official,
                'productionmethod_id': subparcel.productionmethod_id.id,
                'shaded_percentage': subparcel.shaded_percentage,
                'soil_type': subparcel.soil_type,
                'organic_material_percentage':
                    subparcel.organic_material_percentage,
                'orientation': subparcel.orientation,
                'drippers_number': subparcel.drippers_number,
                'drippers_nominal_flow': subparcel.drippers_nominal_flow,
                'plantation_year': subparcel.plantation_year,
                'cultivation_age': subparcel.cultivation_age,
                'age_category': subparcel.age_category,
                })
            subparcel.subparcel_modified = False

    @api.model
    def run_process_incoming_mail(self):
        # Get params
        email_from, subject, only_to_admin, col_date, col_et0, col_pe = \
            self._get_incoming_mail_params()
        condition = [('message_type', '=', 'email'),
                     ('email_from', 'ilike', email_from),
                     ('incoming_mail_processed', '=', False)]
        if subject and subject != '':
            condition.append(('subject', 'ilike', subject))
        if only_to_admin:
            condition.append(('create_uid', '=', SUPERUSER_ID))
        # Get the emails to process
        incoming_messages = self.env['mail.message'].search(
            condition, order='create_date asc')
        for incoming_message in (incoming_messages or []):
            excel_file = ''
            excel_name = ''
            for attachment in (incoming_message.attachment_ids or []):
                is_xls = (len(attachment.name) >= 4 and
                          attachment.name[-4:].lower() == '.xls')
                is_xlsx = (len(attachment.name) >= 5 and
                           attachment.name[-5:].lower() == '.xlsx')
                if is_xls or is_xlsx:
                    base_path = config.filestore(self._cr.dbname)
                    if base_path and len(base_path) >= 1:
                        if base_path[-1:] != '/':
                            base_path = base_path + '/'
                        excel_file = base_path + attachment.store_fname
                        excel_name = attachment.name
                    break
            if excel_file != '':
                process_ok = True
                error_message = ''
                preffix_message = _('Mail with agroclimatic data') + '. ' + \
                    _('EMail from') + ': ' + \
                    incoming_message.email_from + ' .' + \
                    _('Subject') + ': ' + \
                    incoming_message.subject + '. ' + \
                    _('Excel file') + ': ' + \
                    excel_name
                suffix_message = _('OK')
                final_date = ''
                et0 = 0
                pe = 0
                try:
                    final_date, et0, pe = self._process_excel(
                        excel_file, col_date, col_et0, col_pe)
                except Exception as e:
                    process_ok = False
                    error_message = str(e)
                if not process_ok:
                    suffix_message = _('ERROR') + ' (' + error_message + ')'
                message = preffix_message + ' ... ' + suffix_message
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(message)
                if final_date != '':
                    # Update control period (calculation trigger)
                    controlperiod = self._get_control_period(final_date)
                    if controlperiod:
                        controlperiod.write({
                            'et0_value': et0,
                            'pe_value': pe,
                            })
            incoming_message.incoming_mail_processed = True
        # If the recipient of the emails is "admin", delete all emails
        # with a subject other than "agroclimatic data".
        if only_to_admin and subject and subject != '':
            self.sudo()._delete_unnecessary_emails_addressed_to_admin(
                email_from, subject)

    def _get_incoming_mail_params(self):
        email_from = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'incoming_mail_email_from')
        if not email_from:
            email_from = 'goinnowater@gmail.com'
        subject = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'incoming_mail_subject')
        if subject:
            subject = subject.strip().lower()
        only_to_admin = self.env['ir.values'].get_default(
            'wua.monitoring.configuration',
            'incoming_mail_only_emails_to_admin')
        col_date = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'incoming_mail_col_finaldate')
        if not col_date:
            col_date = 'Hasta'
        col_et0 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'incoming_mail_col_et0')
        if not col_et0:
            col_et0 = 'ETo'
        col_pe = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'incoming_mail_col_pe')
        if not col_pe:
            col_pe = 'Pe'
        return email_from, subject, only_to_admin, col_date, col_et0, col_pe

    def _process_excel(self, excel_file, col_date, col_et0, col_pe):
        final_date = ''
        et0 = 0
        pe = 0
        workbook = xlrd.open_workbook(excel_file)
        worksheet = workbook.sheet_by_index(0)
        if worksheet.nrows >= 2 and worksheet.nrows >= 3:
            index_col_date = -1
            index_col_et0 = -1
            index_col_pe = -1
            for col_num in range(worksheet.ncols):
                if worksheet.cell(0, col_num).value == col_date:
                    index_col_date = col_num
                if worksheet.cell(0, col_num).value == col_et0:
                    index_col_et0 = col_num
                if worksheet.cell(0, col_num).value == col_pe:
                    index_col_pe = col_num
            if (index_col_date >= 0 and index_col_et0 >= 0 and
               index_col_pe >= 0):
                raw_final_date = str(worksheet.cell(worksheet.nrows - 2,
                                                    index_col_date).value)
                raw_et0 = str(worksheet.cell(worksheet.nrows - 1,
                                             index_col_et0).value)
                raw_pe = str(worksheet.cell(worksheet.nrows - 1,
                                            index_col_pe).value)
                final_date = raw_final_date
                if len(raw_final_date) == 10:
                    final_date = raw_final_date[6:10] + '-' + \
                        raw_final_date[3:5] + '-' + raw_final_date[0:2]
                et0 = float(raw_et0.replace(',', '.'))
                pe = float(raw_pe.replace(',', '.'))
        return final_date, et0, pe

    def _delete_unnecessary_emails_addressed_to_admin(
            self, email_from, subject):
        # First: are there any possible emails to delete?
        # Not ORM. Reason: performance
        self.env.cr.execute("""
            SELECT COUNT(id) FROM mail_message
            WHERE create_uid=1 AND message_type='email' AND model IS NULL
        """)
        num_rows = self.env.cr.fetchone()[0]
        if num_rows == 0:
            return
        # Second: it is necessary to process the emails
        messages_to_delete = self.env['mail.message'].search(
            [('create_uid', '=', SUPERUSER_ID),
             ('message_type', '=', 'email'),
             ('model', '=', False)])
        email_from = email_from.strip().lower()
        subject = subject.strip().lower()
        base_path = config.filestore(self._cr.dbname)
        if base_path and len(base_path) >= 1:
            if base_path[-1:] != '/':
                base_path = base_path + '/'
        for message_to_delete in (messages_to_delete or []):
            emailfrom_of_message = message_to_delete.email_from.strip().lower()
            subject_of_message = message_to_delete.subject.strip().lower()
            if (emailfrom_of_message.find(email_from) == -1 or
               subject_of_message.find(subject) == -1):
                if message_to_delete.attachment_ids:
                    for attachment in message_to_delete.attachment_ids:
                        attachment_file = base_path + attachment.store_fname
                        try:
                            os.remove(attachment_file)
                        except:
                            pass
                message_to_delete.unlink()

    def _get_control_period(self, ref_date):
        resp = None
        controlperiod = self.env['wua.controlperiod'].search(
            [('initial_date', '<=', ref_date),
             ('end_date', '>=', ref_date)])
        if controlperiod:
            resp = controlperiod[0]
        return resp
