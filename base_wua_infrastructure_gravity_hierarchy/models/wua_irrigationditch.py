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
                 'parcel_05_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = ""
            if record.parcel_05_ids:
                number_of_parcels = len(record.parcel_05_ids)
            elif record.parcel_04_ids:
                number_of_parcels = len(record.parcel_04_ids)
            elif record.parcel_03_ids:
                number_of_parcels = len(record.parcel_03_ids)
            elif record.parcel_02_ids:
                number_of_parcels = len(record.parcel_02_ids)
            elif record.parcel_01_ids:
                number_of_parcels = len(record.parcel_01_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('parcel_01_ids', 'parcel_02_ids',
                 'parcel_03_ids', 'parcel_04_ids',
                 'parcel_05_ids', 'parcel_01_ids.area_official',
                 'parcel_02_ids.area_official',
                 'parcel_03_ids.area_official',
                 'parcel_04_ids.area_official',
                 'parcel_05_ids.area_official')
    def _compute_total_affected_area_official(self):
        for record in self:
            total_affected_area_official = 0.0
            if record.parcel_05_ids:
                for parcel in record.parcel_05_ids:
                    total_affected_area_official += parcel.area_official
            elif record.parcel_04_ids:
                for parcel in record.parcel_04_ids:
                    total_affected_area_official += parcel.area_official
            elif record.parcel_03_ids:
                for parcel in record.parcel_03_ids:
                    total_affected_area_official += parcel.area_official
            elif record.parcel_02_ids:
                for parcel in record.parcel_02_ids:
                    total_affected_area_official += parcel.area_official
            elif record.parcel_01_ids:
                for parcel in record.parcel_01_ids:
                    total_affected_area_official += parcel.area_official
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
            condition = ['|', '|', '|', '|',
                         ('id', 'in',
                          current_irrigationditch.parcel_01_ids.ids),
                         ('id', 'in',
                          current_irrigationditch.parcel_02_ids.ids),
                         ('id', 'in',
                          current_irrigationditch.parcel_03_ids.ids),
                         ('id', 'in',
                          current_irrigationditch.parcel_04_ids.ids),
                         ('id', 'in',
                          current_irrigationditch.parcel_05_ids.ids)]
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
