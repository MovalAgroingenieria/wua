# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    quotaperiod_ids = fields.One2many(
        string='Quota Periods',
        comodel_name='wua.quotaperiod',
        inverse_name='agriculturalseason_id')

    number_of_quotaperiods = fields.Integer(
        string='Number of quota periods',
        store=True,
        compute='_compute_number_of_quotaperiods')

    initialized = fields.Boolean(
        string='Initialized',
        store=True,
        compute='_compute_initialized')

    @api.depends('quotaperiod_ids')
    def _compute_number_of_quotaperiods(self):
        for record in self:
            number_of_quotaperiods = 0
            if record.quotaperiod_ids:
                number_of_quotaperiods = len(record.quotaperiod_ids)
            record.number_of_quotaperiods = number_of_quotaperiods

    @api.depends('quotaperiod_ids',
                 'quotaperiod_ids.initial_date', 'quotaperiod_ids.end_date')
    def _compute_initialized(self):
        for record in self:
            initialized = False
            if record.quotaperiod_ids:
                first_quotaperiod = self.env['wua.quotaperiod'].search(
                    [('agriculturalseason_id', '=', record.id)],
                    limit=1, order='initial_date')
                last_quotaperiod = self.env['wua.quotaperiod'].search(
                    [('agriculturalseason_id', '=', record.id)],
                    limit=1, order='initial_date desc')
                if first_quotaperiod and last_quotaperiod:
                    first_quotaperiod = first_quotaperiod[0]
                    last_quotaperiod = last_quotaperiod[0]
                    if (first_quotaperiod.initial_date ==
                       record.initial_date and
                       last_quotaperiod.end_date == record.end_date):
                        quotaperiods = self.env['wua.quotaperiod'].search(
                            [('agriculturalseason_id', '=', record.id)],
                            order='initial_date')
                        error = False
                        if len(quotaperiods) > 1:
                            quotaperiods_data = []
                            for quotaperiod in quotaperiods:
                                quotaperiods_data.append({
                                    'initial_date': quotaperiod.initial_date,
                                    'end_date': quotaperiod.end_date,
                                    })
                            size_of_quotaperiods = len(quotaperiods_data)
                            for i in range(0, size_of_quotaperiods-1):
                                current_end_date = \
                                    quotaperiods_data[i]['end_date']
                                next_initial_date = \
                                    quotaperiods_data[i+1]['initial_date']
                                current_end_date = \
                                    datetime.datetime.strptime(
                                        current_end_date, '%Y-%m-%d')
                                next_current_end_date = current_end_date + \
                                    datetime.timedelta(days=1)
                                next_initial_date = \
                                    datetime.datetime.strptime(
                                        next_initial_date, '%Y-%m-%d')
                                if (next_current_end_date.date() !=
                                   next_initial_date.date()):
                                    error = True
                        if not error:
                            initialized = True
            record.initialized = initialized

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            if (('initial_date' in vals or 'end_date' in vals) and
               self.quotaperiod_ids):
                    raise exceptions.ValidationError(_(
                        'If the agricultural season has any quota period, '
                        'then it is not possible to change its initial or '
                        'end dates.'))
            resp = super(WuaAgriculturalseason, self).write(vals)
            if 'active_agriculturalseason' in vals:
                self._update_active_flag_in_slave_models(
                    self.id, vals['active_agriculturalseason'])
        else:
            resp = super(WuaAgriculturalseason, self).write(vals)
        return resp

    @api.multi
    def action_get_quota_periods(self):
        self.ensure_one()
        if self.quotaperiod_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quotaperiod_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quotaperiod_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quotaperiod_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Quota Periods'),
                'res_model': 'wua.quotaperiod',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.quotaperiod_ids.ids)],
                'context': {'compressed_agriculturalseason': True}
                }
            return act_window

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_partner_quotas'

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        # Provisional
        print 'action_get_hydric_movements'

    # This method changes the "of_active_agriculturalseason" field for
    # slave-models of the "wua.agriculturalseason" model ("wua.quotaperiod",
    # "wua.individualinput", "wua_cession", etc), using SQL (not ORM).
    # Reason: higher performance, versus the computed fields of slave-models.
    def _update_active_flag_in_slave_models(self, agriculturalseason_id,
                                            active_agriculturalseason):
        if agriculturalseason_id:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE wua_quotaperiod
                    SET of_active_agriculturalseason=FALSE WHERE
                    of_active_agriculturalseason=TRUE""")
                if active_agriculturalseason:
                    self.env.cr.execute("""
                        UPDATE wua_quotaperiod
                        SET of_active_agriculturalseason=TRUE WHERE
                        agriculturalseason_id=""" + str(agriculturalseason_id))
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_(
                    'Error when updating records '
                    '(\"of_active_agriculturalseason\" field).'))

    @api.multi
    def name_get(self):
        if self.env.context.get('compressed_agriculturalseason', False):
            result = []
            for record in self:
                result.append((record.id, record.description.strip()))
        else:
            result = super(WuaAgriculturalseason, self).name_get()
        return result
