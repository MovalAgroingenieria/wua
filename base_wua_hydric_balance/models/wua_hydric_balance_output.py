# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WuaHydricBalanceOutput(models.Model):
    _name = 'wua.hydric.balance.output'
    _description = 'Hydric Balance Output'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
    ]

    TYPES_DICT = {
        '01_presconsumption': 'waterconnection_id',
        '02_gravsconsumption': 'irrigationditch_id',
        '03_irrigationreport': 'intake_id',
        '04_flowmeter_consumption': 'flowmeter_id',
    }

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

    output_type = fields.Selection(
        [
            ('01_presconsumption', 'Pressure Consumption'),
            ('02_gravsconsumption', 'Gravity Consumption'),
            ('03_irrigationreport', 'Irrigation Report'),
            ('04_flowmeter_consumption', 'Flowmeter'),
        ],
        string='Output Type',
        required=True,
        index=True,
        default='01_presconsumption',
    )
    output_configured = fields.Boolean(
        string='Configured Element',
        default=False,
    )
    output_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.output.line',
        inverse_name='output_id',
        string='Output Lines',
    )
    selected_output_line_ids = fields.One2many(
        comodel_name='wua.hydric.balance.output.line',
        inverse_name='output_id',
        string='Selected Output Lines',
        domain=[('output_line_selected', '=', True)],
    )
    total_volume = fields.Float(
        string='Total Volume (m³)',
        digits=(32, 4),
        default=0.0,
        compute='_compute_total_volume',
    )

    @api.depends('hydric_balance_id.name', 'output_type')
    def _compute_name(self):
        for record in self:
            record.name = "{}-{}".format(
                record.hydric_balance_id.name,
                record.output_type)

    @api.depends('selected_output_line_ids',
                 'selected_output_line_ids.volume')
    def _compute_total_volume(self):
        for record in self:
            total_output_volume = sum(
                line.volume for line
                in record.selected_output_line_ids
                if line.output_line_selected)
            record.total_volume = total_output_volume

    def _populate_output_waterconnection(self):
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        output_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_output_line
                WHERE output_id=""" + str(output_id))
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_output_line (
                    id, name, create_uid, write_uid, create_date, write_date,
                    output_id, hydric_balance_id, output_line_selected,
                    initial_time, end_time, volume, presconsumption_id,
                    waterconnection_id, hydraulicsector_id
                )
                SELECT nextval('wua_hydric_balance_output_line_id_seq'),
                    %s || pc.id::TEXT,
                    %s, %s, now(), now(),
                    %s, %s, %s,
                    pc.reading_initial_time, pc.reading_end_time,
                    pc.volume_real, pc.id, pc.waterconnection_id,
                    wc.hydraulicsector_id
                FROM wua_presconsumption AS pc
                LEFT JOIN wua_waterconnection AS wc
                ON pc.waterconnection_id = wc.id
                WHERE pc.validated AND NOT pc.cancelled
                AND pc.reading_initial_time <= %s
                AND pc.reading_end_time >= %s
            """, (name_prefix, user_id, user_id, output_id, balance_id,
                  False, end_date, start_date))
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records.'))

    @api.multi
    def _populate_output_irrigationditch(self):
        self.ensure_one()
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        output_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'

        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_output_line
                WHERE output_id = %s
            """, (output_id,))
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_output_line (
                    id, name, create_uid, write_uid, create_date, write_date,
                    output_id, hydric_balance_id, output_line_selected,
                    initial_time, end_time, volume, gravconsumption_id,
                    irrigationditch_id
                )
                SELECT nextval('wua_hydric_balance_output_line_id_seq'),
                    %s || id::TEXT, %s, %s, now(), now(), %s, %s, %s,
                    watering_initial_time, watering_end_time,
                    watering_volume_real, id, irrigationditch_id
                FROM wua_gravconsumption
                WHERE state = 'executed'
                AND watering_initial_time <= %s
                AND watering_end_time >= %s
            """, (name_prefix, user_id, user_id, output_id, balance_id, False,
                  end_date, start_date))

            self.env.cr.commit()
            self.env.invalidate_all()

        except Exception:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records.'))

    @api.multi
    def _populate_output_flowmeter(self):
        self.ensure_one()
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        output_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'

        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_output_line
                WHERE output_id=""" + str(output_id))
            # Intakeconsumptions
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_output_line (
                    id,
                    name,
                    create_uid,
                    write_uid,
                    create_date,
                    write_date,
                    output_id,
                    hydric_balance_id,
                    output_line_selected,
                    initial_time,
                    end_time,
                    volume,
                    intake_id,
                    intakeconsumption_id,
                    flowmeter_id,
                    hydraulicsector_id
                )
                SELECT
                    nextval('wua_hydric_balance_output_line_id_seq'),
                    %s || ic.id::TEXT,
                    %s,
                    %s,
                    now(),
                    now(),
                    %s,
                    %s,
                    %s,
                    ic.reading_initial_time,
                    ic.reading_end_time,
                    ic.volume_real,
                    ic.intake_id,
                    ic.id,
                    ic.flowmeter_id,
                    ihl.hydraulicsector_id
                FROM wua_intakeconsumption AS ic
                LEFT JOIN wua_intake_hydraulicsectorlink AS ihl
                ON ic.intake_id = ihl.intake_id
                WHERE ic.validated
                AND ic.reading_initial_time <= %s
                AND ic.reading_end_time >= %s
            """, (name_prefix, user_id, user_id, output_id,
                  balance_id, False, end_date, start_date))
            # Waterpipeconsumptions
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_output_line (
                    id, name, create_uid, write_uid, create_date, write_date,
                    output_id, hydric_balance_id, output_line_selected,
                    initial_time, end_time, volume, waterpipe_id,
                    waterpipeconsumption_id, flowmeter_id, hydraulicsector_id
                )
                SELECT nextval('wua_hydric_balance_output_line_id_seq'),
                    %s || wpc.id::TEXT,
                    %s, %s, now(), now(),
                    %s, %s, %s,
                    wpc.reading_initial_time, wpc.reading_end_time,
                    wpc.volume_real, wpc.waterpipe_id, wpc.id,
                    wpc.flowmeter_id, wp.hydraulicsector_id
                FROM wua_waterpipeconsumption AS wpc
                LEFT JOIN wua_waterpipe AS wp
                ON wpc.waterpipe_id = wp.id
                WHERE wpc.validated
                AND wpc.reading_initial_time <= %s
                AND wpc.reading_end_time >= %s
            """, (name_prefix, user_id, user_id, output_id, balance_id,
                  False, end_date, start_date))

            self.env.cr.commit()
            self.env.invalidate_all()

        except Exception:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records.'))

    @api.multi
    def _populate_output_intake(self):
        self.ensure_one()
        balance_id = self.hydric_balance_id.id
        start_date = self.hydric_balance_id.initial_date
        end_date = self.hydric_balance_id.end_date
        output_id = self.id
        user_id = self.env.user.id
        name_prefix = self.hydric_balance_id.name + '-' + self.name + '-'

        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                DELETE FROM wua_hydric_balance_output_line
                WHERE output_id = %s
            """, (output_id,))
            self.env.cr.execute("""
                INSERT INTO wua_hydric_balance_output_line (
                    id, name, create_uid, write_uid, create_date, write_date,
                    output_id, hydric_balance_id, output_line_selected,
                    initial_time, end_time, volume, intake_id,
                    irrigationreport_id, hydraulicsector_id, product_id
                )
                SELECT nextval('wua_hydric_balance_output_line_id_seq'),
                    %s || ir.id::TEXT, %s, %s, now(), now(), %s, %s, %s,
                    ir.report_initial_time, ir.report_end_time, ir.volume,
                    ir.intake_id,
                    ir.id,
                    ihl.hydraulicsector_id,
                    ir.product_id
                FROM wua_irrigationreport AS ir
                LEFT JOIN wua_intake_hydraulicsectorlink AS ihl
                ON ir.intake_id = ihl.intake_id
                WHERE ir.state = 'validated'
                AND NOT ir.cancelled
                AND ir.report_initial_time <= %s
                AND ir.report_end_time >= %s
            """, (name_prefix, user_id, user_id, output_id,
                  balance_id, False, end_date, start_date))

            self.env.cr.commit()
            self.env.invalidate_all()

        except Exception as e:
            self.env.cr.rollback()
            raise UserError(_('Error when updating records: %s') % str(e))

    @api.multi
    def _populate_output_items_type(self, output):
        if output.output_type == '01_presconsumption':
            output._populate_output_waterconnection()
        elif output.output_type == '02_gravsconsumption':
            output._populate_output_irrigationditch()
        elif output.output_type == '03_irrigationreport':
            output._populate_output_intake()
        elif output.output_type == '04_flowmeter_consumption':
            output._populate_output_flowmeter()

    @api.multi
    def action_select_output_line(self):
        self.ensure_one()
        if not self.output_configured:
            self._populate_output_items_type(self)
            self.output_configured = True
        id_tree_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_output_line_view_tree').id
        search_view = self.env.ref(
            'base_wua_hydric_balance.'
            'wua_hydric_balance_output_line_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Output Lines'),
            'res_model': 'wua.hydric.balance.output.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["output_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window
