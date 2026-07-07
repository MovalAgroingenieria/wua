# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WuaInvoicesetPlan(models.Model):
    _name = 'wua.invoiceset.plan'
    _description = 'Entity (invoice set calculation plan)'
    _order = 'id desc'

    invoiceset_id = fields.Many2one(
        string='Invoice set',
        comodel_name='wua.invoiceset',
        ondelete='cascade',
        index=True,
        required=True,
    )

    state = fields.Selection(
        selection=[
            ('computing', 'Computing'),
            ('planned', 'Planned'),
            ('materializing', 'Materializing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        string='State',
        default='computing',
        index=True,
    )

    phase = fields.Selection(
        selection=[
            ('select_items', 'Selecting items'),
            ('calc_details', 'Calculating details'),
            ('grouping', 'Grouping'),
            ('product_data', 'Loading product data'),
            ('creating_invoices', 'Creating invoices'),
            ('finalizing', 'Finalizing'),
        ],
        string='Phase',
    )

    line_ids = fields.One2many(
        string='Plan lines',
        comodel_name='wua.invoiceset.plan.line',
        inverse_name='plan_id',
    )

    line_total = fields.Integer(
        string='Planned invoices',
        default=0,
    )

    line_done = fields.Integer(
        string='Invoices created',
        compute='_compute_progress',
    )

    progress = fields.Float(
        string='Progress',
        compute='_compute_progress',
    )

    details_json = fields.Text(
        string='Invoice details (JSON)',
    )

    validate_after = fields.Boolean(
        string='Validate after materialize',
        default=False,
    )

    date_start = fields.Datetime(string='Start date')

    date_planned = fields.Datetime(string='Planned date')

    date_done = fields.Datetime(string='Done date')

    job_uuid = fields.Char(string='Job UUID', index=True)

    error_info = fields.Text(string='Error info')

    def _compute_progress(self):
        for record in self:
            done = 0
            if record.id:
                record.env.cr.execute(
                    """
                    SELECT count(*)
                    FROM wua_invoiceset_plan_line
                    WHERE plan_id = %s
                      AND state = 'done'
                    """,
                    (record.id,),
                )
                done = record.env.cr.fetchone()[0]
            record.line_done = done
            if record.line_total > 0:
                record.progress = 100.0 * done / record.line_total
            else:
                record.progress = 0.0


class WuaInvoicesetPlanLine(models.Model):
    _name = 'wua.invoiceset.plan.line'
    _description = 'Entity (invoice set plan line)'
    _order = 'sequence, id'

    plan_id = fields.Many2one(
        string='Plan',
        comodel_name='wua.invoiceset.plan',
        ondelete='cascade',
        index=True,
        required=True,
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        index=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('error', 'Error'),
        ],
        string='State',
        default='draft',
        index=True,
    )

    invoice_data_json = fields.Text(string='Invoice data (JSON)')

    invoice_id = fields.Many2one(
        string='Invoice',
        comodel_name='account.invoice',
    )

    error_info = fields.Text(string='Error info')

    sequence = fields.Integer(string='Sequence', default=10)
