# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from odoo import models, fields, api, _


class WuaWaterpipeconsumption(models.Model):
    _inherit = 'wua.waterpipeconsumption'

    network_efficiency = fields.Float(
        string="Network Efficiency (%)",
        digits=(32, 2),
        default=0,
        readonly=True)

    presconsumption_ids = fields.Many2many(
        string='Water-pipe Consumptions',
        comodel_name='wua.presconsumption',
        relation='wua_wpcons_prescons_rel',
        column1='wpcons_id', column2='prescons_id')

    number_of_presconsumptions = fields.Integer(
        string='Number of pressure consumptions',
        compute='_compute_number_of_presconsumptions')

    presconsumptions_total_vol_real = fields.Float(
        string='Vol. total prescons (m³)',
        digits=(32, 4),
        readonly=True)

    vols_difference = fields.Float(
        string='Difference (m³)',
        digits=(32, 4),
        readonly=True)

    @api.depends('presconsumption_ids')
    def _compute_number_of_presconsumptions(self):
        for record in self:
            record.number_of_presconsumptions = \
                len(record.presconsumption_ids)

    @api.multi
    def action_see_wp_presconsumptions(self):
        self.ensure_one()
        id_form_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_view_form').id
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation.'
                                   'wua_presconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Water-pipe Consumptions'),
            'res_model': 'wua.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': [('id', 'in', self.presconsumption_ids.ids)],
            'target': 'current',
            }
        return act_window

    @api.multi
    def refresh_hydric_efficiency(self):
        self.ensure_one()
        self.populate_network_efficiency()

    @api.multi
    def refresh_hydric_efficiency_multi(self, active_ids):
        if active_ids:
            for active_id in active_ids:
                record = self.env['wua.waterpipeconsumption'].browse(active_id)
                record.refresh_hydric_efficiency()

    @api.multi
    def refresh_hydric_efficiency_all(self):
        records = self.env['wua.waterpipeconsumption'].search([])
        if records:
            for record in records:
                record.refresh_hydric_efficiency()

    @api.multi
    def populate_network_efficiency(self):
        error_margin_for_sync_consumptions = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'error_margin_for_sync_consumptions')
        for record in self:
            wpconsumption = record
            self._regenerate_presconsumption_ids(
                wpconsumption, error_margin_for_sync_consumptions)
            network_efficiency = 0
            output_volume = 0
            input_volume = 0
            if wpconsumption.volume_real > 0 and \
                    wpconsumption.presconsumption_ids:
                input_volume = wpconsumption.volume_real
                for presconsumption in wpconsumption.presconsumption_ids:
                    output_volume = output_volume + presconsumption.volume_real
                network_efficiency = output_volume / input_volume
            wpconsumption.network_efficiency = network_efficiency * 100
            wpconsumption.presconsumptions_total_vol_real = output_volume
            wpconsumption.vols_difference = input_volume - output_volume

    @api.model
    def _regenerate_presconsumption_ids(
            self, wpconsumption, error_margin_for_sync_consumptions):
        wpconsumption.write({'presconsumption_ids': [(6, 0, [])]})
        implied_irrigationsheds = self._get_irrigationsheds(
            wpconsumption.waterpipe_id)
        if implied_irrigationsheds:
            reading_initial_time = \
                datetime.strptime(wpconsumption.reading_initial_time,
                                  '%Y-%m-%d %H:%M:%S')
            reading_end_time = \
                datetime.strptime(wpconsumption.reading_end_time,
                                  '%Y-%m-%d %H:%M:%S')
            error_margin_time = \
                timedelta(minutes=error_margin_for_sync_consumptions)
            min_time = str(reading_initial_time - error_margin_time)
            max_time = str(reading_end_time + error_margin_time)
            for irrigationshed in implied_irrigationsheds:
                presconsumptions = self.env['wua.presconsumption'].search(
                    [('irrigationshed_id', '=', irrigationshed.id),
                     ('reading_initial_time', '>=', min_time),
                     ('reading_end_time', '<=', max_time),
                     ('validated', '=', True)])
                for presconsumption in (presconsumptions or []):
                    wpconsumption.write(
                        {'presconsumption_ids': [(4, [presconsumption.id])]})

    @api.model
    def _get_irrigationsheds(self, waterpipe):
        resp = []
        # Irrigation sheds directly connected
        for irrigationshed in (waterpipe.irrigationshed_ids or []):
            resp.append(irrigationshed)
        # Irrigation sheds of descendant water pipes
        for descendant_waterpipe in (waterpipe.waterpipe_ids or []):
            resp.extend(self._get_irrigationsheds(descendant_waterpipe))
        return resp

    @api.model
    def create(self, vals):
        new_waterpipeconsumption = \
            super(WuaWaterpipeconsumption, self).create(vals)
        self.populate_network_efficiency()
        return new_waterpipeconsumption

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            resp = super(WuaWaterpipeconsumption, self).write(vals)
            if 'adjustement_volume' in vals:
                self.populate_network_efficiency()
            return resp
        else:
            return super(WuaWaterpipeconsumption, self).write(vals)
