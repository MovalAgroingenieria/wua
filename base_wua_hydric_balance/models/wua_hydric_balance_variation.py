# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WuaHydricBalanceVariation(models.Model):
    _name = 'wua.hydric.balance.variation'
    _description = 'Hydric Balance Variation'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
    ]

    TYPES_DICT = {'01_reservoir_reading': 'reservoir_id'}

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
    variation_type = fields.Selection(
        [('01_reservoir_reading', 'Reservoir Reading')],
        string='Variation Type',
        required=True,
        index=True,
        default='01_reservoir_reading',
    )
    variation_configured = fields.Boolean(
        string='Configured Element',
        default=False,
    )
    variation_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.variation.line',
        inverse_name='variation_id',
        string='Variation Lines',
    )
    selected_variation_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.variation.line',
        inverse_name='variation_id',
        string='Selected Variation Lines',
        domain=[('variation_line_selected', '=', True)],
    )
    total_volume = fields.Float(
        string='Total Volume (m³)',
        digits=(32, 4),
        default=0.0,
        compute='_compute_total_volume',
    )

    @api.depends('hydric_balance_id.name', 'variation_type')
    def _compute_name(self):
        for record in self:
            record.name = "{}-{}".format(
                record.hydric_balance_id.name,
                record.variation_type,
            )

    @api.depends('selected_variation_line_ids',
                 'selected_variation_line_ids.volume')
    def _compute_total_volume(self):
        for record in self:
            total_variation_volume = sum(
                line.variation_volume for line
                in record.selected_variation_line_ids
                if line.variation_line_selected)
            record.total_volume = total_variation_volume

    def _populate_variation_reservoir(self):
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        variation_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_variation_line
                WHERE variation_id = %s
            """, (variation_id,))
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_variation_line (
                    id, name, create_uid, write_uid, create_date, write_date,
                    variation_id, hydric_balance_id, variation_line_selected,
                    variation_time, volume, variation_volume,
                    reservoirreading_id, reservoir_id
                )
                SELECT
                    nextval('wua_hydric_balance_variation_line_id_seq'),
                    %s || id::TEXT,
                    %s,
                    %s,
                    now(),
                    now(),
                    %s,
                    %s,
                    %s,
                    reading_time,
                    volume,
                    COALESCE(volume - LAG(volume, 1)
                    OVER (PARTITION BY reservoir_id ORDER BY reading_time), 0),
                    id,
                    reservoir_id
                FROM wua_reservoirreading
                WHERE reading_time >= %s
                AND reading_time <= %s
            """, (
                name_prefix, user_id, user_id,
                variation_id, balance_id, False,
                start_date, end_date,
            ))
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records.'))

    def _populate_variation_items_type(self, variation):
        # Method for inherit and extend
        if (variation.variation_type == '01_reservoir_reading'):
            variation._populate_variation_reservoir()

    @api.multi
    def action_select_variation_line(self):
        self.ensure_one()
        if not self.variation_configured:
            self._populate_variation_items_type(self)
            self.variation_configured = True
        id_tree_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_variation_line_view_tree').id
        search_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_variation_line_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Variation Lines'),
            'res_model': 'wua.hydric.balance.variation.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["variation_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window
