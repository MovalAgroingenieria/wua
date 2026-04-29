# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import json
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _name = 'wua.reading'
    _description = 'Entity (reading)'
    _order = 'reading_time desc, name'

    MAX_SIZE_NAME = 52

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        required=True,
        ondelete='restrict')

    reading_time = fields.Datetime(
        string='Time',
        required=True)

    presconsumption_id = fields.Many2one(
        string='Consumption',
        comodel_name='wua.presconsumption',
        readonly=True,
        ondelete='restrict')

    volume = fields.Float(
        string='Value (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    name = fields.Char(
        string='Reading',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    initialization_reading = fields.Boolean(
        string='Initialization Reading',
        default=False,
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='WUA Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
    )

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

    is_last_reading = fields.Boolean(
        string='Last Reading',
        compute='_compute_is_last_reading',
        search='_search_is_last_reading',
    )

    presconsumption_volume = fields.Float(
        string='Gross Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_volume')

    presconsumption_adjustement_volume = fields.Float(
        string='Adjust. Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_adjustement_volume')

    presconsumption_volume_real = fields.Float(
        string='Real Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_volume_real')

    notes = fields.Html(string='Notes')

    validated = fields.Boolean(
        string='Validated Reading',
        default=True,
        required=True)

    last_reading_value = fields.Float(
        string='Last Reading Value (m³)',
        digits=(32, 4),
        default=0,
        compute='_compute_last_reading_value',
    )

    last_reading_time = fields.Datetime(
        string='Last Reading (time)',
        compute='_compute_last_reading_time',
    )

    reading_type = fields.Selection(
        [
            ('01_estimated', 'Estimated Reading'),
            ('02_real_worker', 'Real Worker Reading'),
            ('03_real_partner', 'Real Partner Reading'),
        ],
        string='Reading Type',
        default='01_estimated',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Reading.'),
        ('non_negative_volume', 'CHECK (volume >= 0)',
         'The reading volume must be a non-negative value.'),
        ]

    @api.multi
    @api.depends('waterconnection_id', 'waterconnection_id.last_reading_value')
    def _compute_last_reading_value(self):
        # Batch: prefetch waterconnection_id and last_reading_value
        waterconnections = self.mapped('waterconnection_id')
        if waterconnections:
            waterconnections.mapped('last_reading_value')
        for record in self:
            last_reading_value = 0
            if record.waterconnection_id:
                last_reading_value = \
                    record.waterconnection_id.last_reading_value
            record.last_reading_value = last_reading_value

    @api.multi
    @api.depends('waterconnection_id', 'waterconnection_id.last_reading_time')
    def _compute_last_reading_time(self):
        # Batch: prefetch waterconnection_id and last_reading_time
        waterconnections = self.mapped('waterconnection_id')
        if waterconnections:
            waterconnections.mapped('last_reading_time')
        for record in self:
            last_reading_time = None
            if record.waterconnection_id:
                last_reading_time = record.waterconnection_id.last_reading_time
            record.last_reading_time = last_reading_time

    @api.depends('watermeter_id')
    def _compute_hydraulic_infrastructure_data(self):
        # Batch: prefetch watermeter -> waterconnection, irrigationshed, hydraulicsector, partner
        watermeters = self.mapped('watermeter_id')
        if watermeters:
            watermeters.mapped('waterconnection_id')
            watermeters.mapped('irrigationshed_id')
            watermeters.mapped('hydraulicsector_id')
            watermeters.mapped('waterconnection_id').mapped('partner_id')
        for record in self:
            waterconnection_id_value = None
            irrigationshed_id_value = None
            hydraulicsector_value = None
            partner_id_value = None
            if record.watermeter_id:
                waterconnection_id_value = \
                    record.watermeter_id.waterconnection_id
                irrigationshed_id_value = \
                    record.watermeter_id.irrigationshed_id
                hydraulicsector_value = \
                    record.watermeter_id.hydraulicsector_id
                if (waterconnection_id_value):
                    partner_id_value = waterconnection_id_value.partner_id
            record.waterconnection_id = waterconnection_id_value
            record.irrigationshed_id = irrigationshed_id_value
            record.hydraulicsector_id = hydraulicsector_value
            record.partner_id = partner_id_value

    @api.depends('reading_time', 'watermeter_id')
    def _compute_name(self):
        # Batch: prefetch watermeter_id.name
        watermeters = self.mapped('watermeter_id')
        if watermeters:
            watermeters.mapped('name')
        for record in self:
            value = ''
            if record.watermeter_id and record.reading_time:
                value = record.watermeter_id.name + ' - ' + \
                    record.reading_time
            record.name = value

    @api.multi
    def _compute_is_last_reading(self):
        # Batch: prefetch watermeter_id and last_reading_time
        watermeters = self.mapped('watermeter_id')
        if watermeters:
            watermeters.mapped('last_reading_time')
        for record in self:
            is_last_reading = False
            if (record.watermeter_id and
                    record.watermeter_id.last_reading_time):
                is_last_reading = record.reading_time == \
                    record.watermeter_id.last_reading_time
            record.is_last_reading = is_last_reading

    @api.depends('presconsumption_id', 'presconsumption_id.volume')
    def _compute_presconsumption_volume(self):
        # Batch: prefetch presconsumption_id.volume
        presconsumptions = self.mapped('presconsumption_id')
        if presconsumptions:
            presconsumptions.mapped('volume')
        for record in self:
            presconsumption_volume = 0
            if record.presconsumption_id:
                presconsumption_volume = record.presconsumption_id.volume
            record.presconsumption_volume = presconsumption_volume

    @api.depends('presconsumption_id', 'presconsumption_id.adjustement_volume')
    def _compute_presconsumption_adjustement_volume(self):
        # Batch: prefetch presconsumption_id.adjustement_volume
        presconsumptions = self.mapped('presconsumption_id')
        if presconsumptions:
            presconsumptions.mapped('adjustement_volume')
        for record in self:
            presconsumption_adjustement_volume = 0
            if record.presconsumption_id:
                presconsumption_adjustement_volume = \
                    record.presconsumption_id.adjustement_volume
            record.presconsumption_adjustement_volume = \
                presconsumption_adjustement_volume

    @api.depends('presconsumption_id', 'presconsumption_id.volume_real')
    def _compute_presconsumption_volume_real(self):
        # Batch: prefetch presconsumption_id.volume_real
        presconsumptions = self.mapped('presconsumption_id')
        if presconsumptions:
            presconsumptions.mapped('volume_real')
        for record in self:
            presconsumption_volume_real = 0
            if record.presconsumption_id:
                presconsumption_volume_real = \
                    record.presconsumption_id.volume_real
            record.presconsumption_volume_real = presconsumption_volume_real

    def _search_is_last_reading(self, operator, value):
        domain = [('id', '=', 0)]
        sql_query = """
            SELECT wr1.id
            FROM wua_reading wr1
            INNER JOIN wua_watermeter ww1 ON wr1.watermeter_id = ww1.id
            WHERE wr1.reading_time = ww1.last_reading_time
        """
        self.env.cr.execute(sql_query)
        result = [rec[0] for rec in self.env.cr.fetchall()]
        if operator == '=' and value:
            domain = [('id', 'in', result)]
        elif operator == '=' and not value:
            domain = [('id', 'not in', result)]
        elif operator == '!=' and value:
            domain = [('id', 'not in', result)]
        elif operator == '!=' and not value:
            domain = [('id', 'in', result)]
        return domain

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'volume' in fields:
            fields.remove('volume')
        return super(WuaReading, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        new_presconsumption = None
        reading_end_time = vals['reading_time']
        end_volume = vals['volume']
        # New consumption.
        ctx = self.env.context
        prev_by_wm = ctx.get('estimated_wizard_previous_reading') or {}
        init_wm_ids = ctx.get('estimated_wizard_init_watermeter_ids') or frozenset()
        if not vals['initialization_reading']:
            wm_id = vals['watermeter_id']
            if wm_id in prev_by_wm:
                prev = prev_by_wm[wm_id]
                reading_initial_time = prev['reading_time']
                initial_volume = prev['volume']
                presconsumption_vals = {
                    'reading_initial_time': reading_initial_time,
                    'initial_volume': initial_volume,
                    'reading_end_time': reading_end_time,
                    'end_volume': end_volume,
                }
                new_presconsumption = self.env['wua.presconsumption'].create(
                    presconsumption_vals)
            else:
                reading_initial_time = reading_end_time
                initial_volume = end_volume
                previous_reading = self.env['wua.reading'].search(
                    [('watermeter_id', '=', vals['watermeter_id']),
                     ('reading_time', '<', reading_end_time)],
                    limit=1, order='reading_time desc')
                last_reading = self.env['wua.reading'].search(
                    [('watermeter_id', '=', vals['watermeter_id'])],
                    limit=1, order='reading_time desc')
                if (not last_reading or not previous_reading or last_reading.id !=
                        previous_reading.id):
                    watermeter = self.env['wua.watermeter'].browse(
                        vals['watermeter_id'])
                    watermeter_label = (
                        watermeter.display_name
                        if watermeter else vals['watermeter_id'])
                    if last_reading:
                        raise exceptions.UserError(_(
                            "The new reading time (%s) for water meter '%s'"
                            " is earlier than or equal to the last existing"
                            " reading (%s). Readings must be entered in"
                            " chronological order.") % (
                                reading_end_time,
                                watermeter_label,
                                last_reading.reading_time))
                    else:
                        raise exceptions.UserError(_(
                            "There is no previous reading for water meter"
                            " '%s' before %s. The first reading of a water"
                            " meter must be marked as 'Initialization"
                            " reading'.") % (
                                watermeter_label, reading_end_time))
                reading_initial_time = previous_reading[0].reading_time
                initial_volume = previous_reading[0].volume
                presconsumption_vals = {
                    'reading_initial_time': reading_initial_time,
                    'initial_volume': initial_volume,
                    'reading_end_time': reading_end_time,
                    'end_volume': end_volume,
                }
                new_presconsumption = self.env['wua.presconsumption'].create(
                    presconsumption_vals)
        else:
            if vals['watermeter_id'] in init_wm_ids:
                pass  # No previous reading; skip search and check
            else:
                last_reading = self.env['wua.reading'].search(
                    [('watermeter_id', '=', vals['watermeter_id'])],
                    limit=1, order='reading_time desc')
                if (last_reading and last_reading.reading_time >
                        reading_end_time):
                    watermeter = self.env['wua.watermeter'].browse(
                        vals['watermeter_id'])
                    watermeter_label = (
                        watermeter.display_name
                        if watermeter else vals['watermeter_id'])
                    raise exceptions.UserError(_(
                        "The new initialization reading time (%s) for water"
                        " meter '%s' is earlier than the last existing"
                        " reading (%s). Readings must be entered in"
                        " chronological order.") % (
                            reading_end_time,
                            watermeter_label,
                            last_reading.reading_time))
        if new_presconsumption is not None:
            vals['presconsumption_id'] = new_presconsumption.id
        # Updating the "last_reading_time" and "last_reading_value" fields
        # of the watermeter (skipped when wizard will do a batch update).
        skip_wm_write = ctx.get('estimated_wizard_skip_watermeter_write')
        if not skip_wm_write:
            watermeter = self.env['wua.watermeter'].browse(vals['watermeter_id'])
            if watermeter:
                if new_presconsumption:
                    vals_watermeter = {
                        'last_reading_time': reading_end_time,
                        'last_reading_value': end_volume,
                        'last_reading_consumption':
                            new_presconsumption.volume_real}
                else:
                    vals_watermeter = {
                        'last_reading_time': reading_end_time,
                        'last_reading_value': end_volume,
                        'last_reading_consumption': 0}
                if 'reading_type' in vals:
                    vals_watermeter['last_reading_type'] = vals['reading_type']
                watermeter.write(vals_watermeter)
        # Creation of reading.
        new_reading = super(WuaReading, self).create(vals)
        # Here Presconsumption have the reference to the reading
        pres_id = new_reading.presconsumption_id
        if (pres_id) and not ctx.get('estimated_wizard_defer_perunitareas'):
            pres_id.update_volume_perunitareas()
        return new_reading

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaReading, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        management_of_reading_type = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'management_of_reading_type')
        if not management_of_reading_type and view_type in [
                'form', 'tree', 'search']:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='reading_type']"):
                node.set('invisible', '1')
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['tree_invisible'] = True
                modifiers['column_invisible'] = True
                modifiers['invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
            if view_type == 'search':
                for filter_node in doc.xpath(
                        "//filter[@domain][contains(@domain, "
                        "'reading_type')]"):
                    parent = filter_node.getparent()
                    parent.remove(filter_node)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.multi
    def write(self, vals):
        resp = super(WuaReading, self).write(vals)
        if len(self) == 1:
            if 'volume' in vals:
                if self.presconsumption_id:
                    self.presconsumption_id.write({
                        'end_volume': vals['volume'],
                    })
                    self.presconsumption_id.update_volume_perunitareas()
                self.watermeter_id.last_reading_value = vals['volume']
            if ('reading_type' in vals and
                    self.watermeter_id.last_reading_time == self.reading_time):
                self.watermeter_id.last_reading_type = self.reading_type
            if 'last_reading_consumption' in vals:
                self.watermeter_id.last_reading_consumption = \
                    vals['last_reading_consumption']
        return resp

    @api.multi
    def validate_reading(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_reading(self):
        self.ensure_one()
        if not self.presconsumption_id.invoiced_consumption:
            self.validated = False
        else:
            raise exceptions.UserError(_('The reading is mapped to a '
                                         'invoiced consumption: it is not '
                                         'possible to cancel the reading.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            watermeter_name = record.watermeter_id.name
            reading_time = \
                fields.Datetime.from_string(record.reading_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_time)
                reading_time = reading_time + offset
            reading_time_str = str(reading_time)
            date_str = reading_time_str[:10]
            hour_str = reading_time_str[-8:]
            date_str_localized = self.env['wua.parcel'].\
                transform_date_to_locale(date_str)
            name = watermeter_name + ' - ' + date_str_localized + \
                ' ' + hour_str
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        # Special case: delete a single reading, and the water meter of that
        # reading only has that reading.
        if len(self) == 1:
            watermeter = self.watermeter_id
            readings_of_watermeter = self.env['wua.reading'].search(
                [('watermeter_id', '=', watermeter.id)])
            if len(readings_of_watermeter) == 1:
                resp = super(WuaReading, self).unlink()
                watermeter.unlink()
                return resp
        # Loop to get the oldest reading to delete, and also the newest one.
        watermeter = None
        older_reading_time = None
        newest_reading_time = None
        newest_reading = None
        error_watermeter = False
        readings_to_delete = 0
        for record in self:
            readings_to_delete = readings_to_delete + 1
            if watermeter is None:
                watermeter = record.watermeter_id
                older_reading_time = record.reading_time
                newest_reading_time = older_reading_time
                newest_reading = record
            else:
                if record.watermeter_id == watermeter:
                    if record.reading_time < older_reading_time:
                        older_reading_time = record.reading_time
                    if record.reading_time > newest_reading_time:
                        newest_reading_time = record.reading_time
                        newest_reading = record
                else:
                    error_watermeter = True
                    break
        if error_watermeter:
            raise exceptions.UserError(_('There are different water meters.'))
        if not newest_reading.is_last_reading:
            raise exceptions.UserError(_('There can be no final readings '
                                         'without eliminating.'))
        # Get the time of the new "last-reading".
        readings = self.env['wua.reading']
        new_last_reading = readings.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '<', older_reading_time)],
            limit=1, order="reading_time desc")
        # There should not be readings after the new "last-reading".
        readings_after_new_last_reading = readings.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '>=', older_reading_time),
             ('reading_time', '<=', newest_reading_time)])
        if len(readings_after_new_last_reading) != readings_to_delete:
            raise exceptions.UserError(_('There can be no intermediate '
                                         'readings without eliminating.'))
        # Delete the readings.
        resp = super(WuaReading, self).unlink()
        # Update the "last-reading" and "last-volume" of the water meter from
        # the new "last-reading".
        new_last_reading_time = None
        new_last_reading_type = None
        new_last_reading_value = 0
        new_last_reading_consumption = 0
        if new_last_reading:
            new_last_reading_time = new_last_reading.reading_time
            new_last_reading_value = new_last_reading.volume
            new_last_reading_consumption = \
                new_last_reading.presconsumption_volume_real
            new_last_reading_type = new_last_reading.reading_type
        vals_watermeter = {
            'last_reading_time': new_last_reading_time,
            'last_reading_value': new_last_reading_value,
            'last_reading_consumption': new_last_reading_consumption,
            'last_reading_type': new_last_reading_type,
        }
        watermeter.write(vals_watermeter)
        return resp

    def is_negative_reading(self, reading, reading_time=False):
        is_negative = False
        negative_volume = 0
        current_volume = reading['volume']
        if (not reading_time):
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
        previous_reading = self.env['wua.reading'].search(
            [('watermeter_id', '=', reading['watermeter_id']),
             ('reading_time', '<', reading_time)],
            limit=1, order='reading_time desc')
        if previous_reading:
            previous_volume = previous_reading[0].volume
            if previous_volume > current_volume:
                is_negative = True
                negative_volume = current_volume - previous_volume
        return is_negative, negative_volume

    def validate_readings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.reading'].browse(active_readings)
        for reading in readings:
            if not reading.validated:
                reading.validate_reading()

    def cancel_readings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.reading'].browse(active_readings)
        for reading in readings:
            if reading.validated:
                reading.cancel_reading()
