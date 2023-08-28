# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFertconsumptionset(models.Model):
    _name = 'wua.fertconsumptionset'
    _description = 'Entity (fertilizer consumption lot)'

    MAX_SIZE_NAME = 54

    name = fields.Char(
        string='Description',
        size=MAX_SIZE_NAME,
        index=True,
        required=True,
    )

    notes = fields.Html(
        string='Notes',
    )

    number_of_fertconsumptions = fields.Integer(
        string='Fertconsumptions',
        readonly=True,
        index=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        digits=(32, 4),
        store=True,
        compute='_compute_total_amount'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ], string='State',
        default='draft',
        track_visibility='onchange',
    )

    active = fields.Boolean(
        default=True,
    )

    line_ids = fields.One2many(
        string='Lines',
        comodel_name='wua.fertconsumptionset.line',
        inverse_name='fertconsumptionset_id',
    )

    fertconsumption_ids = fields.One2many(
        string='Fertilizer Consumptions',
        comodel_name='wua.fertconsumption',
        inverse_name='fertconsumptionset_id',
    )

    configured_fertconsumptionset = fields.Boolean(
        string="Configured",
        store=True,
        compute='_compute_configured_fertconsumptionset',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Fertconsumption Lot.'),
    ]

    @api.depends('line_ids', 'line_ids.configured_line')
    def _compute_configured_fertconsumptionset(self):
        for record in self:
            configured = len(record.line_ids) > 0
            if configured:
                for line in record.line_ids:
                    if not line.configured_line:
                        configured = False
                        break
            record.configured_fertconsumptionset = configured

    @api.depends('line_ids', 'line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            total_amount = 0
            if record.line_ids:
                total_amount = sum(record.line_ids.mapped(lambda x: x.amount))
            record.total_amount = total_amount

    # Force the unlink of fertconsumptions (Like a cascade, but we need the
    # ORM)
    @api.multi
    def unlink(self):
        for record in self:
            for fertconsumption in record.fertconsumption_ids:
                if fertconsumption.validated:
                    raise exceptions.UserError(_(
                        'You cannot delete fertconsumption-set if there is '
                        'a validated fertconsumption.'))
            record.fertconsumption_ids.with_context(force_unlink=True).unlink()
        return super(WuaFertconsumptionset, self).unlink()

    @api.multi
    def configure_fertconsumptionset(self):
        self.ensure_one()
        view_id = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer_massive_'
            'assignment.wua_config_fertconsumptionset_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Configuration of Fertconsumption-Set Lines'),
            'res_model': 'wua.fertconsumptionset',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'res_id': self.id,
            }
        return act_window

    @api.multi
    def cancel_fertconsumptionset(self):
        for record in self:
            for fertconsumption in record.fertconsumption_ids:
                if fertconsumption.validated:
                    raise exceptions.UserError(_(
                        'You cannot cancel a fertconsumption-set if there is '
                        'a validated fertconsumption.'))
            record.fertconsumption_ids.with_context(force_unlink=True).unlink()
            fertconsumptionset_vals = {
                'state': 'draft',
                'number_of_fertconsumptions': 0,
                }
            record.write(fertconsumptionset_vals)

    @api.multi
    def calculate_fertconsumptionset(self):
        for record in self:
            total_fertconsumptions = 0
            for line in record.line_ids:
                # Some selected presconsumptions
                if (line.selected_fertconsumptionsetpresconsumption_ids and
                    len(line.selected_fertconsumptionsetpresconsumption_ids) >
                        0):
                    number_of_fertconsumptions = 0
                    accumulated_amount = 0.0
                    n_selected = len(
                        line.selected_fertconsumptionsetpresconsumption_ids)
                    for fert_line in line.\
                            selected_fertconsumptionsetpresconsumption_ids:
                        # If last fert use the rest to ensure no missing amount
                        if (number_of_fertconsumptions == n_selected - 1):
                            fert_amount = round(
                                line.amount - round(accumulated_amount, 4), 4)
                        # Amount is prorated by volume of each consumption
                        else:
                            fert_amount = round(
                                (line.amount * fert_line.volume_real) /
                                line.total_volume, 4)
                            accumulated_amount += fert_amount
                        if (fert_amount > 0):
                            self.env['wua.fertconsumption'].create({
                                'presconsumption_id':
                                    fert_line.presconsumption_id.id,
                                'product_id': line.product_id.id,
                                'amount': fert_amount,
                                'fertconsumptionset_id': record.id,
                                'validated': False,
                            })
                            number_of_fertconsumptions += 1
                            total_fertconsumptions += 1
            record.write({
                'state': 'generated',
                'number_of_fertconsumptions':
                    total_fertconsumptions,
                })

    @api.multi
    def action_see_fertconsumptions(self):
        self.ensure_one()
        condition = [('fertconsumptionset_id', '=', self.id)]
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_form').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Fertconsumptions'),
            'res_model': 'wua.fertconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window


class WuaFertconsumptionsetLine(models.Model):
    _name = 'wua.fertconsumptionset.line'
    _description = 'Fertilizer Consumption Set Line'
    _order = 'name'
    MAX_NAME_SIZE = 150

    fertconsumptionset_id = fields.Many2one(
        string='Fertilizer Consumption Set',
        required=True,
        index=True,
        comodel_name='wua.fertconsumptionset',
        ondelete='cascade',
    )

    product_id = fields.Many2one(
        string='Fertilizer',
        comodel_name='product.product',
        index=True,
        required=True,
        ondelete='restrict',
        domain=[('categ_id.productcategory_code', '=', 12)],
    )

    uom_id = fields.Many2one(
        string='Unit of measure',
        comodel_name='product.uom',
        ondelete='restrict',
        store=False,
        compute='_compute_uom_id',
    )

    amount = fields.Float(
        string='Amount',
        digits=(32, 4),
        required=True,
        index=True,
        default=0.0,
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        required=True,
        index=True,
        comodel_name='wua.hydraulicsector',
        ondelete='restrict',
    )

    name = fields.Char(
        string='Fertilizer Consumption Set Line',
        size=MAX_NAME_SIZE,
        store=True,
        index=True,
        compute='_compute_name',
    )

    fertconsumptionsetpresconsumption_ids = fields.One2many(
        string='Presconsumptions of fertilizer consumption set line',
        comodel_name='wua.fertconsumptionset.line.presconsumption',
        inverse_name='fertconsumptionsetline_id',
    )

    selected_fertconsumptionsetpresconsumption_ids = fields.One2many(
        string='Selected presconsumptions of fertilizer consumption set line',
        comodel_name='wua.fertconsumptionset.line.presconsumption',
        inverse_name='fertconsumptionsetline_id',
        domain=[('selected', '=', True)],
    )

    total_volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
        compute='_compute_total_volume',
        store=True,
    )

    configured_line = fields.Boolean(
        string='Configured',
        store=True,
        compute='_compute_configured_line',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Fertilizer Consumption Line.'),
        ('valid_amount',
         'CHECK (amount > 0)',
         'The Fertilizer Amount must be greater than 0.'),
    ]

    @api.depends('fertconsumptionset_id', 'hydraulicsector_id', 'product_id')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.fertconsumptionset_id and
                    record.hydraulicsector_id and record.product_id):
                name = record.fertconsumptionset_id.name + '-' + \
                    record.product_id.name + '-' + \
                    str(record.hydraulicsector_id.hydraulicsector_code
                        ).zfill(6)
            record.name = name

    @api.depends('fertconsumptionsetpresconsumption_ids',
                 'fertconsumptionsetpresconsumption_ids.selected')
    def _compute_configured_line(self):
        for record in self:
            configured_line = False
            if record.selected_fertconsumptionsetpresconsumption_ids:
                configured_line = True
            record.configured_line = configured_line

    @api.depends('product_id')
    def _compute_uom_id(self):
        for record in self:
            uom_id = None
            if (record.product_id):
                uom_id = record.product_id.uom_id
            record.uom_id = uom_id

    @api.depends('fertconsumptionsetpresconsumption_ids',
                 'fertconsumptionsetpresconsumption_ids.selected')
    def _compute_total_volume(self):
        for record in self:
            total_volume = None
            if (record.selected_fertconsumptionsetpresconsumption_ids):
                total_volume = sum(
                    record.
                    selected_fertconsumptionsetpresconsumption_ids.mapped(
                        lambda x: x.volume_real))
            record.total_volume = total_volume

    def _populate_items_select(self, previous_presc_not_selected=[]):
        presconsumptions = self.env['wua.presconsumption'].search([], limit=1)
        if len(presconsumptions) > 0:
            user_id = self.env.user.id
            fertconsumptionset_id = self.fertconsumptionset_id.id
            fertconsumptionsetline_id = self.id
            hydraulicsector_id = self.hydraulicsector_id.id
            # If we have a previous selection (Refreshing), if the
            # presconsumption was not selected, then it should noit be selected
            # New ones and already selected ones whill be selected
            # -1 Because empty () will be an error
            previous_presc_not_selected.append('-1')
            select_statement = ' CASE WHEN id IN (' + \
                ','.join(previous_presc_not_selected) + ') THEN FALSE ' + \
                'ELSE TRUE END'
            # TODO: This will be better as an extension in other module with
            # invoicing module as dependency
            hmov_condition = ' AND TRUE'
            hmov_invoicing_module = self.env['ir.module.module'].search(
                [('name', '=', 'base_wua_invoicing_hydricmovement')])
            if (not hmov_invoicing_module or
                    hmov_invoicing_module.state != 'installed'):
                hmov_condition = ' AND NOT invoiced_consumption_quota'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM wua_fertconsumptionset_line_presconsumption
                    WHERE fertconsumptionsetline_id=""" + str(
                    fertconsumptionsetline_id))
                self.env.cr.execute(
                    """
                    INSERT INTO wua_fertconsumptionset_line_presconsumption
                    (id, create_uid, write_uid, create_date, write_date,
                    fertconsumptionset_id,
                    fertconsumptionsetline_id, selected, presconsumption_id,
                    reading_id, reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real)
                    SELECT nextval(
                    'wua_fertconsumptionset_line_presconsumption_id_seq'), %s,
                    %s, now(), now(), %s, %s, """ + select_statement +
                    """, id, reading_id,
                    reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real
                    FROM wua_presconsumption
                    WHERE hydraulicsector_id = %s AND
                    validated AND NOT invoiced_consumption
                    """ + hmov_condition, (
                        user_id, user_id, fertconsumptionset_id,
                        fertconsumptionsetline_id, hydraulicsector_id))
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    @api.multi
    def action_refresh_fertconsumptionset_line_presconsumptions(self):
        self.ensure_one()
        return self.action_select_fertconsumptionset_line_presconsumptions(
            {}, True)

    # Context needed because when clicked from the view is always passed
    @api.multi
    def action_select_fertconsumptionset_line_presconsumptions(
            self, context, refresh=False):
        self.ensure_one()
        if not self.configured_line or refresh:
            presconsumptions_not_selected = []
            if (refresh):
                presconsumptions_not_selected = \
                    self.fertconsumptionsetpresconsumption_ids.\
                    filtered(lambda x: not x.selected).mapped(
                        lambda x: str(x.presconsumption_id.id))
            self._populate_items_select(presconsumptions_not_selected)
            self._compute_configured_line()
            self._compute_total_volume()
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer_'
            'massive_assignment.'
            'wua_fertconsumptionset_line_presconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer_'
            'massive_assignment.'
            'wua_fertconsumptionset_line_presconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Presconsumption') +
            ' (' + self.hydraulicsector_id.name + ')',
            'res_model': 'wua.fertconsumptionset.line.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["fertconsumptionsetline_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window


class WuaFertconsumptionsetLinePresconsumption(models.Model):
    _name = 'wua.fertconsumptionset.line.presconsumption'
    _description = 'Pressure consumptions of a fertconsumption-set line'
    _order = 'fertconsumptionsetline_id,presconsumption_id'

    fertconsumptionset_id = fields.Many2one(
        string='Fertilizer Consumption Lot',
        comodel_name='wua.fertconsumptionset',
        required=True,
        ondelete='cascade',)

    fertconsumptionsetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.fertconsumptionset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    presconsumption_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.presconsumption',
        required=True,
        ondelete='restrict')

    reading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.reading',
        ondelete='restrict')

    reading_initial_time = fields.Datetime(
        string='Reading Start Time')

    initial_volume = fields.Float(
        string='Initial Value (m³)',
        digits=(32, 4), default=0)

    reading_end_time = fields.Datetime(
        string='Reading End Time')

    end_volume = fields.Float(
        string='Final Value (m³)',
        digits=(32, 4), default=0)

    volume = fields.Float(
        string='Gross Value (m³)',
        digits=(32, 4), default=0)

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        ondelete='restrict')

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    adjustement_volume = fields.Float(
        string='Adjust. Value (m³)',
        digits=(32, 4), default=0)

    volume_real = fields.Float(
        string='Real Value (m³)',
        digits=(32, 4), default=0)

    @api.multi
    def add_to_fertconsumptionset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_fertconsumptionset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)
