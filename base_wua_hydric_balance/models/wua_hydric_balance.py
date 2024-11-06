# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class WuaHydricBalance(models.Model):
    _name = 'wua.hydric.balance'
    _inherit = 'mail.thread'
    _description = 'Hydric Balance'
    _order = 'name desc'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
        ('check_loss_percentage', 'CHECK(loss_percentage >= 0)',
         'Loss percentage must be non-negative.'),
        ('check_date', 'CHECK(end_date >= initial_date)',
         'End date must be greater than or equal to initial date.'),
    ]

    SIZE_ANNUALSEQ_CODE = 4

    def _default_hydric_balance_name(self):
        resp = ''
        current_year = datetime.datetime.now().year
        full_prefix = str(current_year).zfill(4) + '/'
        resp = full_prefix + '1'.zfill(self.SIZE_ANNUALSEQ_CODE)
        balances = self.search([('name', 'like', full_prefix)],
                               limit=1, order='name desc')
        if len(balances) == 1:
            last_code = balances[0].name
            if len(last_code) > len(full_prefix):
                numeric_suffix = \
                    last_code[-(len(last_code) - len(full_prefix)):]
                try:
                    proposed_code = int(numeric_suffix)
                except Exception:
                    proposed_code = 0
                if proposed_code > 0:
                    resp = full_prefix + \
                        str(proposed_code + 1).zfill(
                            self.SIZE_ANNUALSEQ_CODE)
        return resp

    name = fields.Char(
        string='Code',
        required=True,
        default=lambda self: self._default_hydric_balance_name(),
        index=True,
        unique=True,
    )
    initial_date = fields.Date(
        string='Initial Date',
        required=True,
    )
    end_date = fields.Date(
        string='Final Date',
        required=True,
        default=fields.Date.context_today,
    )
    description = fields.Char(
        string='Description',
        required=True,
        index=True,
    )
    loss_percentage = fields.Float(
        string='Loss percentage',
        digits=(32, 4),
        required=True,
        default=0.00,
    )
    total_loss_percentage = fields.Float(
        string='Loss percentage',
        digits=(32, 4),
        compute='_compute_total_loss_percentage',
        store=True,
    )
    estimated_loss = fields.Float(
        string='Estimated Loss',
        compute='_compute_estimated_loss',
        digits=(32, 2),
        store=True,
    )
    balance_state = fields.Selection(
        [('01_draft', 'Draft'), ('02_computed', 'Computed')],
        string='Balance State',
        default='01_draft',
        copy=False,
        index=True,
        track_visibility='onchange',
        store=True,
    )
    total_input_volume = fields.Float(
        string='Total input (m³)',
        digits=(32, 4),
        readonly=True,
        default=0.00,
    )
    total_output_volume = fields.Float(
        string='Total output (m³)',
        digits=(32, 4),
        readonly=True,
        default=0.00,
    )
    total_variation_volume = fields.Float(
        string='Total variation (m³)',
        digits=(32, 4),
        readonly=True,
        default=0.00,
    )
    difference_volume = fields.Float(
        string='Volume difference (m³)',
        digits=(32, 4),
        compute='_compute_difference_volume',
        store=True,
    )
    notes = fields.Html(
        string='Notes',
    )
    hydric_balance_input_ids = fields.One2many(
        comodel_name='wua.hydric.balance.input',
        inverse_name='hydric_balance_id',
        string='Input elements',
    )
    hydric_balance_output_ids = fields.One2many(
        comodel_name='wua.hydric.balance.output',
        inverse_name='hydric_balance_id',
        string='Output elements',
    )
    hydric_balance_variation_ids = fields.One2many(
        comodel_name='wua.hydric.balance.variation',
        inverse_name='hydric_balance_id',
        string='Variation elements',
    )
    balance_configured = fields.Boolean(
        string='Configured balance',
        compute='_compute_balance_configured',
        store=True,
    )
    hydric_balance_result_ids = fields.One2many(
        comodel_name='wua.hydric.balance.result',
        inverse_name='hydric_balance_id',
        string='Results',
    )

    @api.depends('total_input_volume', 'total_output_volume',
                 'total_variation_volume', 'loss_percentage')
    def _compute_difference_volume(self):
        for record in self:
            record.difference_volume = -(
                record.total_input_volume -
                record.total_output_volume -
                record.total_variation_volume -
                ((record.loss_percentage / 100) * record.total_input_volume)
            )

    @api.depends('hydric_balance_input_ids', 'hydric_balance_output_ids',
                 'hydric_balance_variation_ids',
                 'hydric_balance_input_ids.input_configured',
                 'hydric_balance_output_ids.output_configured',
                 'hydric_balance_variation_ids.variation_configured')
    def _compute_balance_configured(self):
        for record in self:
            configured = any(
                input_record.input_configured
                for input_record in record.hydric_balance_input_ids
            ) or any(
                output_record.output_configured
                for output_record in record.hydric_balance_output_ids
            ) or any(
                variation_record.variation_configured
                for variation_record in record.hydric_balance_variation_ids
            )
            record.balance_configured = configured

    @api.depends('total_input_volume', 'total_output_volume',
                 'total_variation_volume')
    def _compute_total_loss_percentage(self):
        for record in self:
            if record.total_input_volume != 0:
                record.total_loss_percentage = (
                    (record.total_output_volume -
                     record.total_input_volume +
                     record.total_variation_volume) /
                    record.total_input_volume
                ) * 100
            else:
                record.total_loss_percentage = 0

    @api.depends('loss_percentage', 'total_input_volume')
    def _compute_estimated_loss(self):
        for record in self:
            if record.total_input_volume != 0:
                record.estimated_loss = (record.loss_percentage / 100) * \
                    (record.total_input_volume)
            else:
                record.estimated_loss = 0

    @api.multi
    def copy_hydric_balance(self):
        self.ensure_one()

        if self.balance_state != '01_draft':
            raise UserError(
                _('The hydric balance can only be copied in the draft state.'))

        self._do_copy(self)

    def _do_copy(self, new_initial_date, new_end_date):
        copy_vals = {
            'name': self._default_hydric_balance_name(),
            'initial_date': new_initial_date,
            'end_date': new_end_date,
            'description': self.description + ' Copy',
            'loss_percentage': self.loss_percentage,
            'balance_state': '01_draft',
            'total_input_volume': 0,
            'total_output_volume': 0,
            'total_variation_volume': 0,
            'difference_volume': 0,
        }

        new_hydric_balance = self.env['wua.hydric.balance'].create(copy_vals)

        for input_record in self.hydric_balance_input_ids:
            input_record.copy({
                'hydric_balance_id': new_hydric_balance.id,
                'input_configured': False,
            })

        for output_record in self.hydric_balance_output_ids:
            output_record.copy({
                'hydric_balance_id': new_hydric_balance.id,
                'output_configured': False,
            })

        for variation_record in self.hydric_balance_variation_ids:
            variation_record.copy({
                'hydric_balance_id': new_hydric_balance.id,
                'variation_configured': False,
            })

        return new_hydric_balance

    @api.multi
    def action_see_hydric_balance_results(self):
        self.ensure_one()
        condition = [('hydric_balance_id', '=', self.id)]

        id_tree_view = self.env.ref(
            'base_wua_hydric_balance.wua_hydric_balance_result_view_tree').id
        id_pivot_view = self.env.ref(
            'base_wua_hydric_balance.wua_hydric_balance_result_view_pivot').id
        search_view = self.env.ref(
            'base_wua_hydric_balance.wua_hydric_balance_result_view_search')

        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Line Results'),
            'res_model': 'wua.hydric.balance.result',
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'views': [(id_tree_view, 'tree'), (id_pivot_view, 'pivot')],
            'search_view_id': search_view.id,
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.multi
    def calculate_hydric_balance(self):
        self.ensure_one()
        total_input_volume = 0.0
        total_output_volume = 0.0
        total_variation_volume = 0.0
        result_lines = []

        # Inputs
        for input_element in self.hydric_balance_input_ids:
            element_volumes = {}
            if input_element.input_configured:
                for line in input_element.selected_input_line_ids:
                    element_name_field = \
                        input_element.TYPES_DICT.get(input_element.input_type)
                    if element_name_field:
                        element_name = line[element_name_field].name
                        if element_name not in element_volumes:
                            element_volumes[element_name] = {
                                'volume': 0.0,
                                'field_id': line[element_name_field].id,
                            }
                        element_volumes[element_name]['volume'] += line.volume
                for element_name, data in element_volumes.items():
                    result_lines.append({
                        'hydric_balance_id': self.id,
                        'element_name': element_name,
                        '{}'.format(element_name_field): data['field_id'],
                        'result_type': '01_input',
                        'input_type': input_element.input_type,
                        'volume': (data['volume'] -
                                   data['volume'] * self.loss_percentage *
                                   0.01),
                        'initial_volume': 0.0,
                        'end_volume': data['volume'],
                    })
                    total_input_volume += data['volume']

        # Outputs
        for output_element in self.hydric_balance_output_ids:
            element_volumes = {}
            if output_element.output_configured:
                for line in output_element.selected_output_line_ids:
                    element_name_field = \
                        output_element.TYPES_DICT.get(
                            output_element.output_type)
                    if element_name_field:
                        element_name = line[element_name_field].name
                        if element_name not in element_volumes:
                            element_volumes[element_name] = {
                                'volume': 0.0,
                                'field_id': line[element_name_field].id,
                            }
                        element_volumes[element_name]['volume'] += line.volume
                for element_name, data in element_volumes.items():
                    result_lines.append({
                        'hydric_balance_id': self.id,
                        'element_name': element_name,
                        '{}'.format(element_name_field): data['field_id'],
                        'result_type': '02_output',
                        'output_type': output_element.output_type,
                        'volume': data['volume'] * -1,
                        'initial_volume': 0.0,
                        'end_volume': data['volume'],
                    })
                    total_output_volume += data['volume']

        # Variations
        for variation_element in self.hydric_balance_variation_ids:
            element_variations = {}
            if variation_element.variation_configured:
                for line in variation_element.selected_variation_line_ids:
                    element_name_field =\
                        variation_element.TYPES_DICT.get(
                            variation_element.variation_type)
                    if element_name_field:
                        element_name = line[element_name_field].name
                        if element_name not in element_variations:
                            element_variations[element_name] = {
                                'total_variation_volume': 0.0,
                                'initial_volume': line.volume,
                                'end_volume': line.volume,
                                'field_id': line[element_name_field].id,
                                'is_first_line': True,
                            }
                        element_variations[element_name][
                            'total_variation_volume'
                        ] += line.variation_volume
                        element_variations[element_name]['end_volume'] =\
                            line.volume
                for element_name, data in element_variations.items():
                    result_lines.append({
                        'hydric_balance_id': self.id,
                        'element_name': element_name,
                        '{}'.format(element_name_field): data['field_id'],
                        'result_type': '03_variation',
                        'variation_type': variation_element.variation_type,
                        'volume': data['total_variation_volume'] * -1,
                        'initial_volume': data['initial_volume'],
                        'end_volume': data['end_volume'],
                    })
                    total_variation_volume += data['total_variation_volume']

        # Create result lines
        for result in result_lines:
            self.env['wua.hydric.balance.result'].create(result)

        # Update the hydric balance with total volumes and change state
        self.write({
            'total_input_volume': total_input_volume,
            'total_output_volume': total_output_volume,
            'total_variation_volume': total_variation_volume,
            'balance_state': '02_computed',
        })

    @api.multi
    def action_reset_to_draft(self):
        # Eliminar todas las líneas de resultado
        self.ensure_one()
        self.hydric_balance_result_ids.unlink()

        # Cambiar el estado a 'draft'
        self.write({
            'balance_state': '01_draft',
            'total_input_volume': 0,
            'total_output_volume': 0,
            'total_variation_volume': 0,
        })
