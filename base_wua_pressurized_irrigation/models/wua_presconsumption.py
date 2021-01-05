# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaPresconsumption(models.Model):
    _name = 'wua.presconsumption'
    _description = 'Entity (pressurized consumption)'
    _order = 'reading_end_time desc, name'

    MAX_SIZE_NAME = 52

    reading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.reading',
        inverse_name='presconsumption_id',
        readonly=True)

    reading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.reading',
        store=True,
        compute='_compute_reading_id',
        ondelete='cascade')

    reading_initial_time = fields.Datetime(
        string='Reading Start Time',
        readonly=True,
        index=True)

    initial_volume = fields.Float(
        string='Initial Value (m3)',
        digits=(32, 4),
        readonly=True)

    reading_end_time = fields.Datetime(
        string='Reading End Time',
        readonly=True,
        index=True)

    end_volume = fields.Float(
        string='Final Value (m3)',
        digits=(32, 4),
        readonly=True)

    volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume')

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        store=True,
        compute='_compute_watermeter_id',
        ondelete='restrict')

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        required=True,
        default=0)

    volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume_real')

    name = fields.Char(
        string='Pressurized Consumption',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    notes = fields.Html(string='Notes')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='set null')

    validated = fields.Boolean(
        string='Validated Consumption',
        store=True,
        compute='_compute_validated')

    volume_perunitarea = fields.Float(
        string="Volume (m³/Area U.)",
        digits=(32, 4),
        readonly=True,
        index=True)

    volume_perunitareaandday = fields.Float(
        string="Volume (m³/Area U./day)",
        digits=(32, 4),
        readonly=True,
        index=True)

    volume_perunitarea_hec = fields.Float(
        string="Volume (m³/ha)",
        digits=(32, 4),
        readonly=True,
        index=True)

    volume_perunitareaandday_hec = fields.Float(
        string="Volume (m³/ha/day)",
        digits=(32, 4),
        readonly=True,
        index=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Consumption.'),
        ('valid_reading_limits',
         'CHECK (reading_end_time >= reading_initial_time)',
         'The reading end time must be greather than or equal to '
         'reading initial time.'),
        ('valid_volume',
         'CHECK (volume >= 0)',
         'The consumption volume can not be a negative value.'),
        ]

    @api.depends('reading_ids')
    def _compute_reading_id(self):
        for record in self:
            reading_id = None
            filtered_readings = self.env['wua.reading'].search([
                ('presconsumption_id', '=', record.id)])
            if len(filtered_readings) == 1:
                reading_id = filtered_readings[0].id
                record.reading_id = reading_id

    @api.depends('initial_volume', 'end_volume')
    def _compute_volume(self):
        for record in self:
            record.volume = record.end_volume - record.initial_volume

    @api.depends('reading_id')
    def _compute_watermeter_id(self):
        for record in self:
            if record.reading_id.watermeter_id:
                correct_watermeter_id = \
                    record.reading_id.watermeter_id.state == 'active' and \
                    record.reading_id.watermeter_id.waterconnection_id
                if correct_watermeter_id:
                    record.watermeter_id = record.reading_id.watermeter_id
                else:
                    raise exceptions.UserError(
                        _('The water meter is mandatory, '
                          'it must be active and it must '
                          'have a water connection.'))

    @api.depends('watermeter_id')
    def _compute_hydraulic_infrastructure_data(self):
        for record in self:
            waterconnection_id_value = None
            irrigationshed_id_value = None
            hydraulicsector_value = None
            if record.watermeter_id:
                waterconnection_id_value = \
                    record.watermeter_id.waterconnection_id
                irrigationshed_id_value = \
                    record.watermeter_id.irrigationshed_id
                hydraulicsector_value = \
                    record.watermeter_id.hydraulicsector_id
            record.waterconnection_id = waterconnection_id_value
            record.irrigationshed_id = irrigationshed_id_value
            record.hydraulicsector_id = hydraulicsector_value

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('reading_end_time', 'waterconnection_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.reading_end_time:
                value = record.waterconnection_id.name + ' - ' + \
                    record.reading_end_time
            record.name = value

    @api.depends('reading_id', 'reading_id.validated')
    def _compute_validated(self):
        for record in self:
            validated = False
            if record.reading_id.validated:
                validated = True
            record.validated = validated

    @api.model
    def create(self, vals):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [('initial_date', '<=', vals['reading_end_time']),
             ('end_date', '>=', vals['reading_end_time'])])
        if len(agriculturalseasons) == 1:
            vals['agriculturalseason_id'] = agriculturalseasons[0].id
        new_pres = super(WuaPresconsumption, self).create(vals)
        return new_pres

    @api.multi
    def write(self, vals):
        resp = super(WuaPresconsumption, self).write(vals)
        if len(self) == 1:
            if ('adjustement_volume' in vals):
                self.update_volume_perunitareas()
        return resp

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            waterconnection_name = record.waterconnection_id.name
            reading_end_time = \
                fields.Datetime.from_string(record.reading_end_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_end_time)
                reading_end_time = reading_end_time + offset
            reading_end_time_str = str(reading_end_time)
            date_str = reading_end_time_str[:10]
            hour_str = reading_end_time_str[-8:]
            name = waterconnection_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result

    def action_assign_agriculturalseason_to_consumptions(self):
        presconsumptions = self.env['wua.presconsumption']
        all_presconsumptions = presconsumptions.search([])
        all_presconsumptions.write({
            'agriculturalseason_id': None,
            })
        agriculturalseasons = self.env['wua.agriculturalseason'].search([])
        for agriculturalseason in agriculturalseasons:
            presconsumptions_of_current_season = presconsumptions.search(
                [('reading_end_time', '>=', agriculturalseason.initial_date),
                 ('reading_end_time', '<=', agriculturalseason.end_date)])
            if len(presconsumptions_of_current_season) > 0:
                presconsumptions_of_current_season.write({
                    'agriculturalseason_id': agriculturalseason.id,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaPresconsumption, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        show_volume_perunitareaandday = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'show_volume_perunitareaandday')
        doc = etree.XML(res['arch'])
        area_measurement_name = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_name')
        if not area_measurement_name:
            area_measurement_name = 'ha'
        else:
            area_measurement_name = area_measurement_name.decode(
                'utf_8')
        area_measurement_name = area_measurement_name.lower()
        for node in doc.xpath("//field[@name='volume_perunitarea']"):
            original_label = \
                self.sudo().get_value_from_translation(
                    'base_wua_pressurized_irrigation',
                    self.__class__.volume_perunitarea.string)
            preBar = original_label.find('/')
            if preBar != -1:
                original_label = original_label[:preBar + 1]
            node.set('string',
                     original_label +
                     area_measurement_name + ')')
        for node in doc.xpath("//field[@name='volume_perunitareaandday']"):
            original_label = \
                self.sudo().get_value_from_translation(
                    'base_wua_pressurized_irrigation',
                    self.__class__.volume_perunitareaandday.string)
            preBar = original_label.find('/')
            preBar2 = original_label.find('/', preBar + 1)
            end_label = _('day')
            if preBar2 != -1:
                end_label = original_label[preBar2:]
            if preBar != -1:
                original_label = original_label[:preBar + 1]
            node.set('string',
                     original_label +
                     area_measurement_name + end_label)
        if show_volume_perunitareaandday:
            for node in doc.xpath("//field[@name='volume_perunitarea']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"invisible": true, \
                           "tree_invisible": true}')
        else:
            for node in doc.xpath(
                    "//field[@name='volume_perunitareaandday']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"invisible": true, \
                           "tree_invisible": true}')
        res['arch'] = etree.tostring(doc)
        return res

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp

    def update_volume_perunitareas(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = \
                self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        init_time = datetime.datetime.strptime(self.reading_initial_time,
                                               '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(self.reading_end_time,
                                              '%Y-%m-%d %H:%M:%S')
        days = (end_time - init_time).days
        days = days + 1
        volume_perunitarea = 0
        total_area_official = sum(
            x.parcel_id.area_official for x in
            self.waterconnection_id.irrigationpointwc_ids)
        if total_area_official > 0:
            volume_perunitarea = self.volume_real / total_area_official
        volume_perunitarea_hec = volume_perunitarea * factor
        volume_perunitareaandday = volume_perunitarea / days
        volume_perunitareaandday_hec = volume_perunitareaandday * factor
        self.write({
            'volume_perunitarea': volume_perunitarea,
            'volume_perunitarea_hec': volume_perunitarea_hec,
            'volume_perunitareaandday': volume_perunitareaandday,
            'volume_perunitareaandday_hec': volume_perunitareaandday_hec
        })
