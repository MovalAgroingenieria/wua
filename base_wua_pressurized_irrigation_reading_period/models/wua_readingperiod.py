# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from odoo import models, fields, api, exceptions, _


class WuaReadingperiod(models.Model):
    _name = 'wua.readingperiod'
    _description = 'Reading Period'
    _inherit = 'mail.thread'
    _order = 'name'

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
        index=True)

    end_date = fields.Date(
        string='End Date',
        required=True,
        index=True)

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('configured', 'Configured'),
            ('open', 'Opened'),
            ('closed', 'Closed'),
        ],
        string='State',
        index=True,
        default='draft',
        store=True,
        compute='_compute_state',
        track_visibility='onchange')

    name = fields.Char(
        string='Reading Period',
        size=21,
        store=True,
        index=True,
        compute='_compute_name')

    notes = fields.Html(string='Notes')

    readingperiodline_ids = fields.One2many(
        string="Associated Hydraulic-Sectors",
        comodel_name='wua.readingperiod.line',
        inverse_name='readingperiod_id')

    sectors = fields.Char(
        string='Sectors',
        size=100,
        store=True,
        compute='_compute_sectors')

    number_of_irrigationsheds = fields.Integer(
        string='Number of irrigation sheds',
        store=True,
        compute='_compute_number_of_irrigationsheds')

    number_of_waterconnections = fields.Integer(
        string='Number of water connections',
        store=True,
        compute='_compute_number_of_waterconnections')

    reading_ids = fields.One2many(
        string='Associated Readings',
        comodel_name='wua.reading',
        inverse_name='readingperiod_id')

    number_of_readings = fields.Integer(
        string='Number of readings',
        store=True,
        index=True,
        compute='_compute_number_of_readings')

    negative_reading_ids = fields.One2many(
        string='Associated Negative Readings',
        comodel_name='wua.negative.reading',
        inverse_name='readingperiod_id')

    number_of_negative_readings = fields.Integer(
        string='Number of negative readings',
        store=True,
        index=True,
        compute='_compute_number_of_negative_readings')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Reading Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
    ]

    @api.depends('initial_date', 'end_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date + '-' + record.end_date

    @api.depends('initial_date', 'end_date')
    def _compute_agriculturalseason_id(self):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [], order='initial_date desc')
        for record in self:
            agriculturalseason = None
            if (record.initial_date and record.end_date):
                i = 0
                while (i < len(agriculturalseasons) and not
                        agriculturalseason):
                    if(((record.initial_date >=
                        agriculturalseasons[i].initial_date) and
                            (record.end_date <=
                             agriculturalseasons[i].end_date))):
                        agriculturalseason = agriculturalseasons[i]
                    i = i + 1
            record.agriculturalseason_id = agriculturalseason

    @api.depends('reading_ids')
    def _compute_number_of_readings(self):
        for record in self:
            number_of_readings = 0
            if (record.reading_ids):
                number_of_readings = len(record.reading_ids)
            record.number_of_readings = number_of_readings

    @api.depends('negative_reading_ids')
    def _compute_number_of_negative_readings(self):
        for record in self:
            number_of_negative_readings = 0
            if (record.negative_reading_ids):
                number_of_negative_readings = len(record.negative_reading_ids)
            record.number_of_negative_readings = number_of_negative_readings

    @api.depends('readingperiodline_ids',
                 'readingperiodline_ids.hydraulicsector_id')
    def _compute_sectors(self):
        for record in self:
            sectors = []
            if (record.readingperiodline_ids):
                for rpl in record.readingperiodline_ids:
                    if (rpl.hydraulicsector_id and
                            rpl.hydraulicsector_id.name not in sectors):
                        sectors.append(rpl.hydraulicsector_id.name)
            record.sectors = ','.join(sectors)

    @api.depends('readingperiodline_ids',
                 'readingperiodline_ids.number_of_irrigationsheds')
    def _compute_number_of_irrigationsheds(self):
        for record in self:
            number_of_irrigationsheds = 0
            if (record.readingperiodline_ids):
                for rpl in record.readingperiodline_ids:
                    if (rpl.number_of_irrigationsheds):
                        number_of_irrigationsheds = number_of_irrigationsheds \
                            + rpl.number_of_irrigationsheds
            record.number_of_irrigationsheds = number_of_irrigationsheds

    @api.depends('readingperiodline_ids',
                 'readingperiodline_ids.number_of_waterconnections')
    def _compute_number_of_waterconnections(self):
        for record in self:
            number_of_waterconnections = 0
            if (record.readingperiodline_ids):
                for rpl in record.readingperiodline_ids:
                    if (rpl.number_of_waterconnections):
                        number_of_waterconnections = \
                            number_of_waterconnections + \
                            rpl.number_of_waterconnections
            record.number_of_waterconnections = number_of_waterconnections

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1):
            agriculturalseasons = self.env['wua.agriculturalseason'].search([
                ('initial_date', '<=', self.initial_date),
                ('end_date', '>=', self.end_date)
            ])
            if (not agriculturalseasons):
                raise exceptions.ValidationError(_(
                    'The reading period limits are outside of all agricultural'
                    ' seasons.'))

    @api.model
    def create(self, vals):
        model_values = self.env['ir.values'].sudo()
        allow_overlapping_reading_period = model_values.get_default(
            'wua.irrigation.configuration', 'allow_overlapping_reading_period')
        if (not allow_overlapping_reading_period):
            readingperiods = self.env['wua.readingperiod'].search([])
            some_overlapping = False
            i = 0
            while (i < len(readingperiods) and not some_overlapping):
                rp = readingperiods[i]
                some_overlapping = ((vals['initial_date'] >=
                                     rp.initial_date and
                                    vals['initial_date'] <= rp.end_date) or
                                    (vals['end_date'] >= rp.initial_date and
                                    vals['end_date'] <= rp.end_date))
                i = i + 1
            if (some_overlapping):
                raise exceptions.UserError(_(
                    'The reading period limits overlaps with another reading'
                    ' period.'))
        return super(WuaReadingperiod, self).create(vals)

    @api.multi
    def action_get_reading_ids(self):
        self.ensure_one()
        condition = [('readingperiod_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_reading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_reading_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_reading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Readings'),
            'res_model': 'wua.reading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.multi
    def action_get_negative_reading_ids(self):
        self.ensure_one()
        condition = [('readingperiod_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_negative_reading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_negative_reading_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_negative_reading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Negative Readings'),
            'res_model': 'wua.negative.reading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.depends('readingperiodline_ids',
                 'readingperiodline_ids.configured_line')
    def _compute_state(self):
        for record in self:
            state = 'draft'
            if record.readingperiodline_ids:
                configured_lines = True
                for readingperiodline in record.readingperiodline_ids:
                    if not readingperiodline.configured_line:
                        configured_lines = False
                        break
                if configured_lines:
                    state = 'configured'
            record.state = state

    @api.multi
    def action_configure_readingperiod(self):
        self.ensure_one()
        view_id = self.env.ref(
            'base_wua_pressurized_irrigation_reading_period'
            '.wua_config_readingperiod_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Configuration of Reading-Period Lines'),
            'res_model': 'wua.readingperiod',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'res_id': self.id,
        }
        return act_window

    @api.multi
    def action_open_readingperiod(self):
        self.ensure_one()
        rp = self.env['wua.readingperiod'].search([('state', '=', 'open')])
        if (rp):
            raise exceptions.UserError(_(
                'There cannot be more than one open reading period.'))
        readingperiod = self
        self._delete_irrigationshed_assignments(readingperiod,
                                                only_unselected=True)
        self.state = 'open'

    @api.multi
    def action_cancel_readingperiod(self):
        self.ensure_one()
        readingperiod = self
        if (readingperiod.reading_ids or readingperiod.negative_reading_ids):
            raise exceptions.UserError(_(
                'Operation not allowed: this reading period has some '
                'associated readings. Before canceling, it is mandatory to '
                'remove this readings.'))
        self._delete_irrigationshed_assignments(readingperiod,
                                                only_unselected=False)
        self.state = 'draft'

    @api.multi
    def action_close_readingperiod(self):
        self.ensure_one()
        self.state = 'closed'

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        if (self.env.context and 'lang' in self.env.context):
            is_english = self.env.context['lang'] == 'en_US'
        else:
            is_english = True
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
                name = name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    def _delete_irrigationshed_assignments(self, readingperiod,
                                           only_unselected=False):
        if readingperiod:
            readingperiodlines = readingperiod.readingperiodline_ids
            for readingperiodline in readingperiodlines:
                readingperiodline_id = readingperiodline.id
                sf = ''
                if only_unselected:
                    sf = ' AND selected=False'
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                        DELETE FROM wua_readingperiod_line_irrigationshed WHERE
                        readingperiodline_id=""" + str(readingperiodline_id) +
                                        sf)
                    self.env.cr.commit()
                    self.env.invalidate_all()
                except Exception:
                    self.env.cr.rollback()
                    raise exceptions.UserError(
                        _('Error when updating records.'))
                if not only_unselected:
                    readingperiodline._compute_number_of_irrigationsheds()
                    readingperiodline._compute_number_of_waterconnections()
                    readingperiodline._compute_configured_line()


class WuaReadingperiodLine(models.Model):
    _name = 'wua.readingperiod.line'
    _description = 'Reading-Period Line'
    _order = 'name'
    MAX_NAME_SIZE = 28

    readingperiod_id = fields.Many2one(
        string='Reading Period',
        required=True,
        index=True,
        comodel_name='wua.readingperiod',
        ondelete='cascade')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        required=True,
        index=True,
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    name = fields.Char(
        string='Reading-Period Line',
        size=MAX_NAME_SIZE,
        store=True,
        index=True,
        compute='_compute_name')

    readingperiodlineirrigationshed_ids = fields.One2many(
        string='Irrigation sheds of reading-period line',
        comodel_name='wua.readingperiod.line.irrigationshed',
        inverse_name='readingperiodline_id')

    selected_readingperiodlineirrigationshed_ids = fields.One2many(
        string='Selected irrigation sheds of reading-period line',
        comodel_name='wua.readingperiod.line.irrigationshed',
        inverse_name='readingperiodline_id',
        domain=[('selected', '=', True)])

    number_of_irrigationsheds = fields.Integer(
        string='Number of selected irrigation-sheds',
        store=True,
        compute='_compute_number_of_irrigationsheds')

    number_of_waterconnections = fields.Integer(
        string='Number of selected water-connections',
        store=True,
        compute='_compute_number_of_waterconnections')

    configured_line = fields.Boolean(
        string='Configured',
        store=True,
        compute='_compute_configured_line')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Reading-Period Line.')
    ]

    @api.depends('readingperiod_id', 'hydraulicsector_id')
    def _compute_name(self):
        for record in self:
            name = None
            if (record.readingperiod_id and record.hydraulicsector_id):
                name = record.readingperiod_id.name + '-' + \
                    str(record.hydraulicsector_id.hydraulicsector_code
                        ).zfill(6)
            record.name = name

    @api.depends('readingperiodlineirrigationshed_ids',
                 'readingperiodlineirrigationshed_ids.selected')
    def _compute_number_of_irrigationsheds(self):
        for record in self:
            number_of_irrigationsheds = 0
            if record.readingperiodlineirrigationshed_ids:
                filtered_readingperiodlineirrigationshed_ids = filter(
                    lambda x: x['selected'] is True,
                    record.readingperiodlineirrigationshed_ids)
                if filtered_readingperiodlineirrigationshed_ids:
                    number_of_irrigationsheds = \
                        len(filtered_readingperiodlineirrigationshed_ids)
            record.number_of_irrigationsheds = number_of_irrigationsheds

    @api.depends('readingperiodlineirrigationshed_ids',
                 'readingperiodlineirrigationshed_ids.selected')
    def _compute_number_of_waterconnections(self):
        for record in self:
            number_of_waterconnections = 0
            if record.readingperiodlineirrigationshed_ids:
                filtered_readingperiodlineirrigationshed_ids = filter(
                    lambda x: x['selected'] is True,
                    record.readingperiodlineirrigationshed_ids)
                if filtered_readingperiodlineirrigationshed_ids:
                    for rpl_irrigationshed in \
                            filtered_readingperiodlineirrigationshed_ids:
                        if (rpl_irrigationshed.irrigationshed_id and
                            rpl_irrigationshed.irrigationshed_id.
                                waterconnection_ids):
                            number_of_waterconnections = \
                                number_of_waterconnections + \
                                rpl_irrigationshed.number_of_waterconnections
            record.number_of_waterconnections = number_of_waterconnections

    @api.depends('readingperiodlineirrigationshed_ids',
                 'readingperiodlineirrigationshed_ids.selected')
    def _compute_configured_line(self):
        for record in self:
            configured_line = False
            if record.readingperiodlineirrigationshed_ids:
                filtered_readingperiodlineirrigationshed_ids = filter(
                    lambda x: x['selected'] is True,
                    record.readingperiodlineirrigationshed_ids)
                if filtered_readingperiodlineirrigationshed_ids:
                    configured_line = True
            record.configured_line = configured_line

    def _populate_items_select(self, selected=True):
        irrigationsheds = self.env['wua.irrigationshed'].search([])
        if len(irrigationsheds) > 0:
            user_id = self.env.user.id
            readingperiodline_id = self.id
            hydraulicsector_id = self.hydraulicsector_id.id
            selected_val = 'TRUE'
            if not selected:
                selected_val = 'FALSE'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM wua_readingperiod_line_irrigationshed
                    WHERE readingperiodline_id=""" + str(readingperiodline_id))
                self.env.cr.execute("""
                    INSERT INTO wua_readingperiod_line_irrigationshed (id,
                    create_uid, write_uid, create_date, write_date,
                    readingperiodline_id, selected, irrigationshed_id,
                    hydraulicsector_id, elevation, number_of_parcels,
                    number_of_waterconnections,
                    total_affected_area_official_hec)
                    SELECT nextval(
                    'wua_readingperiod_line_irrigationshed_id_seq'), %s,
                    %s, now(), now(), %s, %s, id, hydraulicsector_id,
                    elevation, number_of_parcels, number_of_waterconnections,
                    total_affected_area_official_hec FROM wua_irrigationshed
                    WHERE hydraulicsector_id = %s AND active
                    """, (user_id, user_id, readingperiodline_id, selected_val,
                          hydraulicsector_id))
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    @api.multi
    def action_select_readingperiod_line_irrigationsheds(self):
        self.ensure_one()
        if not self.configured_line:
            self._populate_items_select()
            self.env['wua.readingperiod.line.irrigationshed'].search([]).\
                _compute_readingperiod_id()
            self._compute_number_of_irrigationsheds()
            self._compute_number_of_waterconnections()
            self._compute_configured_line()
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_reading_period.'
            'wua_readingperiod_line_irrigationshed_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_reading_period.'
            'wua_readingperiod_line_irrigationshed_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Irrigationshed') +
            ' (' + self.hydraulicsector_id.name + ')',
            'res_model': 'wua.readingperiod.line.irrigationshed',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["readingperiodline_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window


class WuaReadingperiodLineIrrigationshed(models.Model):
    _name = 'wua.readingperiod.line.irrigationshed'
    _description = 'Reading-Period Line Irrigationshed'
    _order = 'readingperiodline_id,irrigationshed_id'

    readingperiodline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.readingperiod.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string='Selected',
        default=True)

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        required=True,
        ondelete='cascade')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='cascade')

    elevation = fields.Float(
        string='Elevation (m)',
        digits=(7, 2),
        default=0)

    number_of_waterconnections = fields.Integer(
        string='Number of water connections',
        default=0)

    total_affected_area_official_hec = fields.Float(
        string='Cumulative area of parcels',
        digits=(32, 4),
        default=0)

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        default=0)

    readingperiod_id = fields.Many2one(
        string='Reading Period',
        store=True,
        comodel_name='wua.readingperiod',
        index=True,
        compute='_compute_readingperiod_id',
        ondelete='cascade')

    reading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.reading',
        inverse_name='readingperiodlineirrigationshed_id')

    negative_reading_ids = fields.One2many(
        string='Negative Readings',
        comodel_name='wua.negative.reading',
        inverse_name='readingperiodlineirrigationshed_id')

    is_visited = fields.Boolean(
        string='Visited?',
        store=True,
        default=False,
        compute='_compute_is_visited')

    @api.depends('readingperiodline_id')
    def _compute_readingperiod_id(self):
        for record in self:
            readingperiod = None
            if (record.readingperiodline_id):
                readingperiod = record.readingperiodline_id.readingperiod_id
            record.readingperiod_id = readingperiod

    @api.depends('reading_ids', 'negative_reading_ids')
    def _compute_is_visited(self):
        for record in self:
            is_visited = False
            if (record.reading_ids or record.negative_reading_ids):
                is_visited = True
            record.is_visited = is_visited

    @api.multi
    def add_to_readingperiod(self):
        vals = {
            'selected': True,
        }
        self.write(vals)

    @api.multi
    def remove_from_readingperiod(self):
        vals = {
            'selected': False,
        }
        self.write(vals)
