# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    _in_create = False

    hydricmovement_ids = fields.One2many(
        string='Hydric Consumptions',
        comodel_name='wua.hydricmovement',
        inverse_name='irrigationreport_id')

    number_of_hydricmovements = fields.Integer(
        string='Number of hydric mov.',
        compute='_compute_number_of_hydricmovements')

    # This method is reimplemented because in the create method is not
    # available the intake_id field. This computed method is called
    # after the create method.
    def _compute_volume_real(self):
        super(WuaIrrigationReport, self)._compute_volume_real()
        if self.__class__._in_create:
            self.__class__._in_create = False
            quota_model = self.env['wua.quota']
            for record in self:
                quota_model.create_hydricmovements_irrigationreport(record)

    @api.multi
    def _compute_number_of_hydricmovements(self):
        for record in self:
            number_of_hydricmovements = 0
            if record.hydricmovement_ids:
                number_of_hydricmovements = len(record.hydricmovement_ids)
            record.number_of_hydricmovements = number_of_hydricmovements

    @api.model
    def create(self, vals):
        self.__class__._in_create = True
        new_irrigationreport = super(WuaIrrigationReport, self).create(vals)
        return new_irrigationreport

    @api.multi
    def write(self, vals):
        super(WuaIrrigationReport, self).write(vals)
        if len(self) == 1:
            updated_irrigationreport = self
            delete_hydricmovements, create_hydricmovements = \
                self._force_refresh_hydricmovements(updated_irrigationreport,
                                                    vals)
            # It is not possible to create hydric movements and not
            # eliminate previous movements.
            if (create_hydricmovements and (not delete_hydricmovements)):
                create_hydricmovements = False
            if (self.is_valid_irrigationreport(updated_irrigationreport) and
               (not delete_hydricmovements) and (not create_hydricmovements)):
                if ('initial_volume' in vals or 'end_volume' in vals or
                   'hours' in vals or 'adjustement_volume' in vals):
                    delete_hydricmovements = True
                    create_hydricmovements = True
            if delete_hydricmovements or create_hydricmovements:
                quota_model = self.env['wua.quota']
                if delete_hydricmovements:
                    quota_model.delete_hydricmovements_irrigationreport(
                        updated_irrigationreport)
                if create_hydricmovements:
                    quota_model.create_hydricmovements_irrigationreport(
                        updated_irrigationreport)
        return True

    @api.multi
    def unlink(self):
        quotas_to_refresh_ids = []
        for record in self:
            # It is necessary to refresh the affected quotas
            if record.hydricmovement_ids:
                for hydricmovement in record.hydricmovement_ids:
                    quotas_to_refresh_ids.append(hydricmovement.quota_id.id)
                record.hydricmovement_ids.with_context(
                    force_unlink=True).sudo().unlink()
        if quotas_to_refresh_ids:
            quotas_to_refresh_ids = list(set(quotas_to_refresh_ids))
            quotas_to_refresh = self.env['wua.quota'].browse(
                quotas_to_refresh_ids)
            for quota in quotas_to_refresh:
                self.env['wua.quota'].refresh_quota(quota)
        return super(WuaIrrigationReport, self).unlink()

    # Hook
    def is_valid_irrigationreport(self, updated_irrigationreport):
        return True

    # Hook
    def _force_refresh_hydricmovements(self, updated_irrigationreport, vals):
        return False, False

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
                'name': _('Hydric Movements'),
                'res_model': 'wua.hydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovement_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True}
                }
            return act_window
