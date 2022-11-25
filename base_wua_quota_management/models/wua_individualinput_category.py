# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIndividualinputCategory(models.Model):
    _name = 'wua.individualinput.category'
    _description = 'Categories of individual inputs'
    _order = 'category_code'

    SIZE_NAME = 50

    def _default_category_code(self):
        resp = 0
        categories = self.search([], limit=1,
                                 order='category_code desc')
        if categories:
            resp = categories[0].category_code + 1
        else:
            resp = 1
        return resp

    category_code = fields.Integer(
        string='Code',
        default=_default_category_code,
        required=True,
        index=True)

    name = fields.Char(
        string='Name',
        size=SIZE_NAME,
        required=True,
        translate=True,
        index=True)

    superproduct_id = fields.Many2one(
        string='Default Superproduct',
        comodel_name='wua.superproduct',
        index=True,
        ondelete='restrict',)

    is_no_variation_category = fields.Boolean(
        string='WUA Master Individual Input Category',
        default=False)

    is_readonly = fields.Boolean(
        string='WUA Individual Input Category Readonly',
        default=False)

    effective_factor = fields.Float(
        digits=(32, 2),
        string='Effective Factor',
        help='Value from 0 to 1 (default 1). If it is less than 1, '
             'then the volume of hydric movement mapped to a individual input '
             'of this category will be multiplied by this factor',
        default=1,
        required=True)

    individualinput_ids = fields.One2many(
        string='Individual inputs',
        comodel_name='wua.individualinput',
        inverse_name='category_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('valid_category_code', 'CHECK (category_code > 0)',
         'The category code must be a positive value.'),
        ('unique_category_code', 'UNIQUE (category_code)',
         'Existing Category.'),
        ('valid_effective_factor',
         'CHECK (effective_factor > 0 and effective_factor <= 1)',
         'The effective factor must be greater than 0 and less than or '
         'equal to 1.'),
        ]

    @api.constrains('effective_factor')
    def _check_effective_factor(self):
        if len(self) == 1:
            if self.category_code == 1 and self.effective_factor != 1:
                raise exceptions.UserError(
                    _('The \'NO-VARIATION\' category must have an effective '
                      'factor equal to 1.'))

    @api.multi
    def unlink(self):
        for record in self:
            if record.is_no_variation_category or record.is_readonly:
                raise exceptions.UserError(_('It is not possible to remove '
                                             'the \'NO-VARIATION\' category.'))
        res = super(WuaIndividualinputCategory, self).unlink()
        return res

    @api.multi
    def action_get_individualinputs(self):
        self.ensure_one()
        if self.individualinput_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_search')
            id_pivot_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_pivot').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Individual inputs'),
                'res_model': 'wua.individualinput',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'),
                          (id_form_view, 'form'),
                          (id_pivot_view, 'pivot')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.individualinput_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True,
                            'search_default_grouped_quotaperiod': True,
                            'search_default_grouped_partner': True}
                }
            return act_window
