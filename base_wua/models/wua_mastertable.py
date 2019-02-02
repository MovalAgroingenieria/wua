# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaMastertable(models.Model):
    _name = 'wua.mastertable'
    _description = 'Master Table with name, description and notes'
    _order = 'name'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 255
    MAX_SIZE_DESCRIPTION = 255

    # Sizes of "name" and "description" in the view form.
    _size_name = 20
    _size_description = 75

    # Is "name" a numeric value?
    _numeric_name = False

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = False

    name = fields.Char(
        string='Name',
        size=MAX_SIZE_NAME,
        required=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ]

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))
        if len(name_no_blanks) > self.__class__._size_name:
            raise exceptions.ValidationError(_('Value too long.'))
        if self.__class__._numeric_name:
            try:
                proposed_numeric_code = int(name_no_blanks)
            except:
                proposed_numeric_code = 0
            if proposed_numeric_code <= 0:
                raise exceptions.ValidationError(_('The field must be '
                                                   'a positive value.'))

    @api.constrains('description')
    def _check_description(self):
        if not self.description:
            return
        description_no_blanks = self.description.strip()
        if len(description_no_blanks) > self.__class__._size_description:
            raise exceptions.ValidationError(
                _('Value too long.'))

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        return super(WuaMastertable, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        return super(WuaMastertable, self).write(vals)

    def refine_name(self, vals):
        name = vals['name']
        if isinstance(name, basestring):
            name = name.strip()
            if self.__class__._lowercase_name:
                name = name.lower()
            if self.__class__._uppercase_name:
                name = name.upper()
            if self.__class__._numeric_name:
                name = name.zfill(self.__class__._size_name)
            vals.update({'name': name})

    def refine_description(self, vals):
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})
