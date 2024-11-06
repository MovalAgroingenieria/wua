# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WuaHydricBalanceInput(models.Model):
    _name = 'wua.hydric.balance.input'
    _description = 'Hydric Balance Input'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
    ]

    TYPES_DICT = {'01_flowmeter_consumption': 'flowmeter_id'}

    name = fields.Char(
        string='Code',
        compute='_compute_name',
        store=True,
        unique=True,
        index=True,
    )
    hydric_balance_id = fields.Many2one(
        comodel_name='wua.hydric.balance',
        string='Balance',
        required=True,
        index=True,
        ondelete='cascade',
    )
    input_type = fields.Selection(
        [('01_flowmeter_consumption', 'Flowmeter Consumption')],
        string='Input Type',
        required=True,
        index=True,
        default='01_flowmeter_consumption',
    )
    input_configured = fields.Boolean(
        string='Configured Element',
        default=False,
    )
    input_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.input.line',
        inverse_name='input_id',
        string='Input Lines',
    )
    selected_input_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.input.line',
        inverse_name='input_id',
        string='Selected Input Lines',
        domain=[('input_line_selected', '=', True)],
    )
    total_volume = fields.Float(
        string='Total Volume (m³)',
        digits=(32, 4),
        default=0.0,
        compute='_compute_total_volume',
    )

    @api.depends('hydric_balance_id.name', 'input_type')
    def _compute_name(self):
        for record in self:
            record.name = "{}-{}".format(
                record.hydric_balance_id.name,
                record.input_type,
            )

    @api.depends('selected_input_line_ids',
                 'selected_input_line_ids.volume')
    def _compute_total_volume(self):
        for record in self:
            total_volume = sum(
                line.volume for line
                in record.selected_input_line_ids
                if line.input_line_selected)
            record.total_volume = total_volume

    def _populate_input_flowmeter(self):
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        input_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_input_line
                WHERE input_id=""" + str(input_id))
            # Intakeconsumptions
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_input_line (
                    id,
                    name,
                    create_uid,
                    write_uid,
                    create_date,
                    write_date,
                    input_id,
                    hydric_balance_id,
                    input_line_selected,
                    initial_time,
                    end_time,
                    volume,
                    intake_id,
                    intakeconsumption_id,
                    flowmeter_id
                )
                SELECT
                    nextval('wua_hydric_balance_input_line_id_seq'),
                    %s || id::TEXT,
                    %s,
                    %s,
                    now(),
                    now(),
                    %s,
                    %s,
                    %s,
                    reading_initial_time,
                    reading_end_time,
                    volume_real,
                    intake_id,
                    id,
                    flowmeter_id
                FROM wua_intakeconsumption
                WHERE validated
                AND reading_initial_time <= %s
                AND reading_end_time >= %s
                """, (name_prefix, user_id,
                      user_id, input_id, balance_id,
                      False, end_date, start_date))
            # Waterpipeconsumptions
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_input_line (id, name,
                create_uid, write_uid, create_date, write_date,
                input_id, hydric_balance_id, input_line_selected,
                initial_time, end_time,
                volume,
                waterpipe_id, waterpipeconsumption_id, flowmeter_id
                )
                SELECT nextval(
                'wua_hydric_balance_input_line_id_seq'), %s || id::TEXT,
                %s,
                %s, now(), now(), %s, %s, %s, reading_initial_time,
                reading_end_time, volume_real, waterpipe_id, id, flowmeter_id
                FROM wua_waterpipeconsumption
                WHERE validated
                AND reading_initial_time <= %s
                AND reading_end_time >= %s
                """, (name_prefix, user_id, user_id, input_id, balance_id,
                      False, end_date, start_date))
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records.'))

    def _populate_input_items_type(self, input):
        # Method for inherit and extend
        if (input.input_type == '01_flowmeter_consumption'):
            input._populate_input_flowmeter()

    @api.multi
    def action_select_input_line(self):
        self.ensure_one()
        if not self.input_configured:
            self._populate_input_items_type(self)
            self.input_configured = True
        id_tree_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_input_line_view_tree').id
        search_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_input_line_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Input Lines'),
            'res_model': 'wua.hydric.balance.input.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["input_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window
