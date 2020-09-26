# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    monitoring = fields.Boolean(
        string='Monitoring',
        default=False)

    lower_age_middle = fields.Integer(
        string='Lower limit for middle cultivation',
        default=2,
        help='If the cultivation age is less than this limit, the '
             'cultivation will be \"litte\"; otherwise it will be \"middle\"')

    upper_age_middle = fields.Integer(
        string='Upper limit for middle cultivation',
        default=4,
        help='If the cultivation age is greater than this limit, the '
             'cultivation will be \"big\"; otherwise it will be \"middle\"')

    kc_ids = fields.One2many(
        string='Kc-Coefficients of cultivation',
        comodel_name='wua.cultivation.kc',
        inverse_name='cultivation_id')

    _sql_constraints = [
        ('valid_lower_age_middle',
         'CHECK (lower_age_middle >= 0)',
         'The \"lower limit for middle cultivation\" must be '
         'a value zero or positive.'),
        ('valid_upper_age_middle',
         'CHECK (upper_age_middle >= lower_age_middle)',
         'The \"upper limit for middle cultivation\" must be '
         'equal to or grater than lower limit.'),
        ]

    @api.multi
    def write(self, vals):
        cultivations_to_update_kc = []
        super(WuaCultivation, self).write(vals)
        if 'monitoring' in vals and vals['monitoring']:
            for record in self:
                if not record.kc_ids:
                    cultivations_to_update_kc.append(record)
        if cultivations_to_update_kc:
            control_periodicity = self.env['ir.values'].get_default(
                'wua.monitoring.configuration', 'control_periodicity')
            if not control_periodicity:
                control_periodicity = 's'
            number_of_periods = 52
            if control_periodicity == 'b':
                number_of_periods = 26
            else:
                if control_periodicity == 'm':
                    number_of_periods = 12
            cultivation_kc_model = self.env['wua.cultivation.kc']
            for cultivation in cultivations_to_update_kc:
                for i in range(number_of_periods):
                    number_of_period = i + 1
                    cultivation_kc_model.create({
                        'period_number': number_of_period,
                        'cultivation_id': cultivation.id})
        return True

    def get_wua_cultivation_comparative_presconsumption_action(self):
        current_cultivation_id = self.env.context.get('active_id')
        condition = [('cultivation_id', '=', current_cultivation_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Cultivations'),
            'res_model': 'wua.comparative.cultivation.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window


    @api.multi
    def action_get_cultivation_kc(self):
        self.ensure_one()
        if self.kc_ids:
            id_tree_view = self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_cultivation_kc_edit_view_tree').id
            search_view = self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_cultivation_kc_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Kc'),
                'res_model': 'wua.cultivation.kc',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.kc_ids.ids)]
                }
            return act_window
