# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIrrigationditch(models.Model):
    _inherit = 'wua.irrigationditch'

    SIZE_PATH = 255

    is_main = fields.Boolean(
        string="Main",
        default=True,
        required=True)

    irrigationditch_id = fields.Many2one(
        string="Supplied by",
        comodel_name="wua.irrigationditch",
        index=True,
        ondelete='restrict')

    irrigationditch_ids = fields.One2many(
        string="Supplied Irrigation ditches",
        comodel_name="wua.irrigationditch",
        inverse_name="irrigationditch_id")

    level = fields.Integer(
        string="Level",
        index=True,
        store=True,
        compute="_compute_level_n_path")

    path = fields.Char(
        string="Full name",
        size=SIZE_PATH,
        index=True,
        store=True,
        compute="_compute_level_n_path")

    parcel_01_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_01_id',
        string="Parcels at level 1 ditch")

    parcel_02_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_02_id',
        string="Parcels at level 2 ditch")

    parcel_03_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_03_id',
        string="Parcels at level 3 ditch")

    parcel_04_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_04_id',
        string="Parcels at level 4 ditch")

    parcel_05_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_05_id',
        string="Parcels at level 5 ditch")

    parcel_06_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_06_id',
        string="Parcels at level 6 ditch")

    parcel_07_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_07_id',
        string="Parcels at level 7 ditch")

    parcel_08_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_08_id',
        string="Parcels at level 8 ditch")

    parcel_09_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_09_id',
        string="Parcels at level 9 ditch")

    parcel_10_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_10_id',
        string="Parcels at level 10 ditch")

    parcel_11_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_11_id',
        string="Parcels at level 11 ditch")

    parcel_12_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_12_id',
        string="Parcels at level 12 ditch")

    parcel_13_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_13_id',
        string="Parcels at level 13 ditch")

    parcel_14_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_14_id',
        string="Parcels at level 14 ditch")

    parcel_15_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_15_id',
        string="Parcels at level 15 ditch")

    parcel_16_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_16_id',
        string="Parcels at level 16 ditch")

    parcel_17_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_17_id',
        string="Parcels at level 17 ditch")

    parcel_18_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_18_id',
        string="Parcels at level 18 ditch")

    parcel_19_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_19_id',
        string="Parcels at level 19 ditch")

    parcel_20_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_20_id',
        string="Parcels at level 20 ditch")

    @api.depends('irrigationditch_id', 'name')
    def _compute_level_n_path(self):
        for record in self:
            path = ''
            if record.name:
                path = record.name
            level = 1
            irrigationditch_mother = record.irrigationditch_id
            while irrigationditch_mother:
                path = irrigationditch_mother.name + '/' + path
                level = level + 1
                irrigationditch_mother = \
                    irrigationditch_mother.irrigationditch_id
            record.path = path
            record.level = level

    @api.depends('parcel_01_ids', 'parcel_02_ids',
                 'parcel_03_ids', 'parcel_04_ids',
                 'parcel_05_ids', 'parcel_06_ids',
                 'parcel_07_ids', 'parcel_08_ids',
                 'parcel_09_ids', 'parcel_10_ids',
                 'parcel_11_ids', 'parcel_12_ids',
                 'parcel_13_ids', 'parcel_14_ids',
                 'parcel_15_ids', 'parcel_16_ids',
                 'parcel_17_ids', 'parcel_18_ids',
                 'parcel_19_ids', 'parcel_20_ids')
    def _compute_number_of_parcels(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_irrigation')
        for record in self:
            number_of_parcels = 0
            level = max_level
            while (number_of_parcels <= 0 and level > 0):
                if record['parcel_' + str(level).zfill(2) + '_ids']:
                    number_of_parcels = len(
                        record['parcel_' + str(level).zfill(2) + '_ids'])
                level -= 1
            record.number_of_parcels = number_of_parcels

    @api.depends('parcel_01_ids', 'parcel_02_ids',
                 'parcel_03_ids', 'parcel_04_ids',
                 'parcel_05_ids', 'parcel_06_ids',
                 'parcel_07_ids', 'parcel_08_ids',
                 'parcel_09_ids', 'parcel_10_ids',
                 'parcel_11_ids', 'parcel_12_ids',
                 'parcel_13_ids', 'parcel_14_ids',
                 'parcel_15_ids', 'parcel_16_ids',
                 'parcel_17_ids', 'parcel_18_ids',
                 'parcel_19_ids', 'parcel_20_ids',
                 'parcel_01_ids.area_official',
                 'parcel_02_ids.area_official',
                 'parcel_03_ids.area_official',
                 'parcel_04_ids.area_official',
                 'parcel_05_ids.area_official',
                 'parcel_06_ids.area_official',
                 'parcel_07_ids.area_official',
                 'parcel_08_ids.area_official',
                 'parcel_09_ids.area_official',
                 'parcel_10_ids.area_official',
                 'parcel_11_ids.area_official',
                 'parcel_12_ids.area_official',
                 'parcel_13_ids.area_official',
                 'parcel_14_ids.area_official',
                 'parcel_15_ids.area_official',
                 'parcel_16_ids.area_official',
                 'parcel_17_ids.area_official',
                 'parcel_18_ids.area_official',
                 'parcel_19_ids.area_official',
                 'parcel_20_ids.area_official')
    def _compute_total_affected_area_official(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_irrigation')
        for record in self:
            total_affected_area_official = 0.0
            level = max_level
            some_level = False
            while (not some_level and level > 0):
                if record['parcel_' + str(level).zfill(2) + '_ids']:
                    some_level = True
                    for parcel in \
                            record['parcel_' + str(level).zfill(2) + '_ids']:
                        total_affected_area_official += parcel.area_official
                level -= 1
            record.total_affected_area_official = total_affected_area_official

    @api.constrains('is_main', 'irrigationditch_id')
    def _check_irrigationditch_id(self):
        if self.is_main and self.irrigationditch_id:
            raise exceptions.ValidationError(_('The main ditch cannot '
                                               'be supplied by any other.'))
        if not self.is_main and not self.irrigationditch_id:
            raise exceptions.ValidationError(_('A non-main ditch must be '
                                               'supplied by another.'))

    @api.constrains('level')
    def _check_level(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_irrigation')
        if self.level > max_level:
            raise exceptions.ValidationError(_('You cannot create a '
                                               'irrigation ditch that depends '
                                               'on a ditch of the highest '
                                               'level (%s).' % max_level))

    @api.model
    def create(self, vals):
        # Prevent character / in the ditch name.
        if ('name' in vals and '/' in vals['name']):
            raise exceptions.ValidationError(_('The character "/" cannot '
                                               'be used in the name of the '
                                               'irrigation ditch.'))
        # Call to inherited method.
        new_irrigationditch = \
            super(WuaIrrigationditch, self).create(vals)
        return new_irrigationditch

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            # Prevent character / in the ditch name.
            if ('name' in vals and '/' in vals['name']):
                raise exceptions.ValidationError(_('The character "/" cannot '
                                                   'be used in the name of '
                                                   'the irrigation ditch.'))
            # Prevent a ditch from connecting with itself
            if ('irrigationditch_id' in vals and
               self.id == vals['irrigationditch_id']):
                raise exceptions.ValidationError(_('A ditch cannot be '
                                                   'supplied by itself.'))
            # Call to inherited method.
            old_name = self.name
            super(WuaIrrigationditch, self).write(vals)
            # If name is changed, update all irrigationditches that
            # contain the old name (except for the current record).
            if 'name' in vals:
                new_name = vals['name']
                irrigationditches = self.env['wua.irrigationditch'].search(
                    [('id', '!=', self.id)])
                for irrigationditch in irrigationditches:
                    path_parts = irrigationditch.path.split('/')
                    new_path = ""
                    if old_name in path_parts:
                        for item in path_parts:
                            if item == old_name:
                                item = new_name
                            if len(path_parts) == 1:
                                new_path += item
                            elif item == path_parts[-1]:
                                new_path += item
                            else:
                                new_path += item + '/'
                        irrigationditch.write({'path': new_path})
            return True
        else:
            return super(WuaIrrigationditch, self).write(vals)

    def get_wua_irrigationditch_parcels_action_gh(self):
        current_irrigationditch_id = self.env.context.get('active_id')
        current_irrigationditch = self.browse(current_irrigationditch_id)
        if current_irrigationditch:
            condition = []
            max_level = self.env['ir.values'].get_default(
                'wua.infrastructure.configuration',
                'max_levels_gravity_irrigation')
            #  Add operator, '|'
            condition.extend(['|'] * (max_level - 1))
            for i in range(1, max_level + 1):
                # Add possible ids
                condition.append(
                    ('id', 'in',
                     current_irrigationditch['parcel_' + str(i).zfill(2) +
                                             '_ids'].ids))
            id_tree_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_tree').id
            id_form_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_form').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Parcels'),
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'domain': condition,
                'target': 'current',
                'context': self.env.context,
                }
            return act_window
