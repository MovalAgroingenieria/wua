# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from odoo import models, fields, api, _


class WuaSuperproduct(models.Model):
    _name = 'wua.superproduct'
    _description = 'Superproduct'
    _inherit = 'mail.thread'
    _inherits = {'product.template': 'product_tmpl_id'}
    _order = 'superproduct_code'

    COLOR_INPUTS = '#4169E1'
    COLOR_OUTPUTS = '#FFA500'
    COLOR_BALANCE = '#696969'

    def _default_superproduct_code(self):
        resp = 0
        superproducts = self.search([], limit=1,
                                    order='superproduct_code desc')
        if superproducts:
            resp = superproducts[0].superproduct_code + 1
        else:
            resp = 1
        return resp

    product_tmpl_id = fields.Many2one(
        string='Related Product',
        help='Product-related data of superproduct',
        required=True,
        ondelete='restrict',
        comodel_name='product.template')

    superproduct_code = fields.Integer(
        string='Code',
        default=_default_superproduct_code,
        required=True,
        index=True)

    is_superproduct = fields.Boolean(
        related='product_tmpl_id.is_superproduct',
        inherited=True,
        default=True)

    type = fields.Selection(
        related='product_tmpl_id.type',
        inherited=True,
        default='service')

    sale_ok = fields.Boolean(
        related='product_tmpl_id.sale_ok',
        inherited=True,
        default=True)

    purchase_ok = fields.Boolean(
        related='product_tmpl_id.purchase_ok',
        inherited=True,
        default=False)

    product_tmpl_ids = fields.One2many(
        string='Associated Products',
        comodel_name='product.template',
        inverse_name='superproduct_id')

    number_of_products = fields.Integer(
        string='Number of products',
        store=True,
        compute='_compute_number_of_products')

    quota_ids = fields.One2many(
        string='Quotas',
        comodel_name='wua.quota',
        inverse_name='superproduct_id')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='superproduct_id')

    active_agriculturalseason_id = fields.Many2one(
        string='Active Agricultural Season',
        comodel_name='wua.agriculturalseason',
        compute='_compute_active_agriculturalseason_id')

    number_of_quotas = fields.Integer(
        string='Number of quotas (active agricultural season)',
        compute='_compute_number_of_quotas')

    number_of_hydricmovements = fields.Integer(
        string='Number of hydric movements (active agricultural season)',
        compute='_compute_number_of_hydricmovements')

    total_input = fields.Float(
        string='Total Input, in m³ (active agricultural season)',
        digits=(32, 2),
        compute='_compute_total_input')

    total_output = fields.Float(
        string='Total Output, in m³ (active agricultural season)',
        digits=(32, 2),
        compute='_compute_total_output')

    balance = fields.Float(
        string='Balance, in m³ (active agricultural season)',
        digits=(32, 2),
        compute='_compute_balance')

    kanban_dashboard_graph_inputs = fields.Text(
        string='Dashboard Graph of inputs for kanban view',
        compute='_compute_kanban_dashboard_graph_inputs')

    kanban_dashboard_graph_outputs = fields.Text(
        string='Dashboard Graph of outputs for kanban view',
        compute='_compute_kanban_dashboard_graph_outputs')

    kanban_dashboard_graph_balance = fields.Text(
        string='Dashboard Graph of balance for kanban view',
        compute='_compute_kanban_dashboard_graph_balance')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('valid_superproduct_code', 'CHECK (superproduct_code > 0)',
         'The superproduct code must be a positive value.'),
        ('unique_superproduct_code', 'UNIQUE (superproduct_code)',
         'Existing Superproduct.'),
        ]

    @api.depends('product_tmpl_ids')
    def _compute_number_of_products(self):
        for record in self:
            number_of_products = 0
            if record.product_tmpl_ids:
                number_of_products = len(record.product_tmpl_ids)
            record.number_of_products = number_of_products

    @api.multi
    def _compute_active_agriculturalseason_id(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            record.active_agriculturalseason_id = active_agriculturalseason_id

    @api.multi
    def _compute_number_of_quotas(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            number_of_quotas = 0
            if active_agriculturalseason_id:
                self.env.cr.execute("""
                    SELECT COUNT(*) FROM wua_quota
                    WHERE agriculturalseason_id=%s AND
                    superproduct_id=%s""", (active_agriculturalseason_id.id,
                                            record.id))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('count') is not None:
                    number_of_quotas = query_results[0].get('count')
            record.number_of_quotas = number_of_quotas

    @api.multi
    def _compute_number_of_hydricmovements(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            number_of_hydricmovements = 0
            if active_agriculturalseason_id:
                self.env.cr.execute("""
                    SELECT COUNT(*) FROM wua_hydricmovement
                    WHERE agriculturalseason_id=%s AND
                    superproduct_id=%s""", (active_agriculturalseason_id.id,
                                            record.id))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('count') is not None:
                    number_of_hydricmovements = query_results[0].get('count')
            record.number_of_hydricmovements = number_of_hydricmovements

    @api.multi
    def _compute_total_input(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            total_input = 0
            if active_agriculturalseason_id:
                self.env.cr.execute("""
                    SELECT SUM(volume) FROM wua_hydricmovement
                    WHERE is_consumption=FALSE AND agriculturalseason_id=%s AND
                    superproduct_id=%s""", (active_agriculturalseason_id.id,
                                            record.id))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') is not None:
                    total_input = query_results[0].get('sum')
            record.total_input = total_input

    @api.multi
    def _compute_total_output(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            total_output = 0
            if active_agriculturalseason_id:
                self.env.cr.execute("""
                    SELECT SUM(volume) FROM wua_hydricmovement
                    WHERE is_consumption=TRUE AND agriculturalseason_id=%s AND
                    superproduct_id=%s""", (active_agriculturalseason_id.id,
                                            record.id))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') is not None:
                    total_output = query_results[0].get('sum')
            record.total_output = total_output

    @api.depends('total_input', 'total_output')
    def _compute_balance(self):
        for record in self:
            record.balance = record.total_input - record.total_output

    @api.multi
    def _compute_kanban_dashboard_graph_inputs(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            record.kanban_dashboard_graph_inputs = json.dumps(
                self._get_data_graph(record, active_agriculturalseason_id,
                                     'inputs'))

    @api.multi
    def _compute_kanban_dashboard_graph_outputs(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            record.kanban_dashboard_graph_outputs = json.dumps(
                self._get_data_graph(record, active_agriculturalseason_id,
                                     'outputs'))

    @api.multi
    def _compute_kanban_dashboard_graph_balance(self):
        active_agriculturalseason_id = \
            self.env['wua.agriculturalseason'].get_active_agriculturalseason()
        for record in self:
            record.kanban_dashboard_graph_balance = json.dumps(
                self._get_data_graph(record, active_agriculturalseason_id))

    @api.multi
    def unlink(self):
        # The ORM does not unlink the product_tmpl_id of a superproduct:
        # it is necessary to unlink manually (SQL), except in the
        # uninstallation (see hooks.py).
        if not self._context.get('uninstall'):
            template_to_unlink_ids = []
            for record in self:
                template_to_unlink_ids.append(record.product_tmpl_id.id)
            resp = super(WuaSuperproduct, self).unlink()
            self.sudo()._force_unlink_residual(template_to_unlink_ids)
        else:
            resp = super(WuaSuperproduct, self).unlink()
        return resp

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        if self.quota_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Quotas') + ' (' + self.name + ')',
                'res_model': 'wua.quota',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.quota_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True,
                            'search_default_not_closed_quotaperiod': True}
                }
            return act_window

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        if self.hydricmovement_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Hydric Movements') + ' (' + self.name + ')',
                'res_model': 'wua.hydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovement_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True,
                            'search_default_not_closed_quotaperiod': True}
                }
            return act_window

    @api.multi
    def action_open_superproduct_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_superproduct_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Superproducts'),
            'res_model': 'wua.superproduct',
            'res_id': self.id,
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'flags': {'mode': 'readonly'}
            }
        return act_window

    @api.multi
    def action_open_active_agriculturalseason_form(self):
        self.ensure_one()
        if self.active_agriculturalseason_id:
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_agriculturalseason_view_form').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Agricultural Seasons'),
                'res_model': 'wua.agriculturalseason',
                'res_id': self.active_agriculturalseason_id.id,
                'view_type': 'form',
                'views': [(id_form_view, 'form')],
                'target': 'current',
                'flags': {'mode': 'readonly'}
                }
            return act_window

    @api.multi
    def action_set_active_agricultural_season(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Choose the active agricultural season'),
            'res_model': 'wizard.set.activeagriculturalseason',
            'src_model': 'wua.superproduct',
            'view_mode': 'form',
            'target': 'new',
            'context': {'refresh_view': True}
            }
        return act_window

    def _get_data_graph(self, superproduct, agriculturalseason,
                        type='balance'):
        if (not superproduct or not agriculturalseason):
            return [{'values': [], 'title': ''}]
        data = []
        ymin, ymax = self._get_limits_for_graphs(superproduct)
        title = _('BALANCE')
        color = self.COLOR_BALANCE
        if type == 'balance':
            inputs = self._get_data_graph(
                superproduct, agriculturalseason, 'inputs')
            outputs = self._get_data_graph(
                superproduct, agriculturalseason, 'outputs')
            data = inputs[0]['values']
            data_outputs = outputs[0]['values']
            length_data = len(data)
            if (data and data_outputs and (length_data == len(data_outputs))):
                data[0]['color'] = color
                for i in range(length_data):
                    data[i]['value'] = \
                        data[i]['value'] - data_outputs[i]['value']
        else:
            title = _('INPUTS')
            condition_is_consumption = 'FALSE'
            color = self.COLOR_INPUTS
            if type == 'outputs':
                title = _('OUTPUTS')
                condition_is_consumption = 'TRUE'
                color = self.COLOR_OUTPUTS
            quotaperiods = self.env['wua.quotaperiod'].search(
                [('agriculturalseason_id', '=', agriculturalseason.id)],
                order='initial_date')
            if quotaperiods:
                number_of_quotaperiods = len(quotaperiods)
                index_current_period = 1
                for quotaperiod in quotaperiods:
                    label = str(index_current_period) + '/' + \
                        str(number_of_quotaperiods)
                    value = 0
                    sql = """
                        SELECT SUM(volume) FROM wua_hydricmovement
                        WHERE is_consumption=%s AND quotaperiod_id=%s AND
                        superproduct_id=%s"""
                    self.env.cr.execute(sql, (condition_is_consumption,
                                              quotaperiod.id, superproduct.id))
                    query_results = self.env.cr.dictfetchall()
                    if (query_results and
                       query_results[0].get('sum') is not None):
                        value = query_results[0].get('sum')
                    node = {'label': label, 'value': value}
                    if index_current_period == 1:
                        node.update({
                            'ymin': ymin, 'ymax': ymax,
                            'color': color
                            })
                    data.append(node)
                    index_current_period = index_current_period + 1
        return [{'values': data, 'title': title}]

    def _get_limits_for_graphs(self, superproduct):
        ymin = -1
        ymax = 0
        # if superproduct.balance < 0:
        #     ymin = -1
        if superproduct.total_input > superproduct.total_output:
            ymax = superproduct.total_input
        else:
            ymax = superproduct.total_output
        ymax = 1.05 * ymax
        return ymin, ymax

    def _force_unlink_residual(self, template_to_unlink_ids):
        if template_to_unlink_ids:
            where = ''
            for item in template_to_unlink_ids:
                where = str(item) + ','
            where = where[:-1]
            where = '(' + where + ')'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM product_template WHERE id in """ + where)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
