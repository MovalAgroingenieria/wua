# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    _in_create = False

    hydricmovement_ids = fields.One2many(
        string='Hydric Consumptions',
        comodel_name='wua.hydricmovement',
        inverse_name='presconsumption_id')

    # This method is reimplemented because in the create method is not
    # available the waterconnection_id field. This computed method is called
    # after the create method.
    def _compute_hydraulic_infrastructure_data(self):
        super(WuaPresconsumption, self)._compute_hydraulic_infrastructure_data(
            )
        if self.__class__._in_create:
            self.__class__._in_create = False
            quota_model = self.env['wua.quota']
            for record in self:
                if self.is_valid_presconsumption(record):
                    quota_model.create_hydricmovements_presconsumption(record)

    @api.model
    def create(self, vals):
        new_presconsumption = super(WuaPresconsumption, self).create(vals)
        self.__class__._in_create = True
        return new_presconsumption

    @api.multi
    def write(self, vals):
        super(WuaPresconsumption, self).write(vals)
        if len(self) == 1:
            updated_presconsumption = self
            delete_hydricmovements, create_hydricmovements = \
                self._force_refresh_hydricmovements(updated_presconsumption,
                                                    vals)
            # It is not possible to create hydric movements and not
            # eliminate previous movements.
            if (create_hydricmovements and (not delete_hydricmovements)):
                create_hydricmovements = False
            if (self.is_valid_presconsumption(updated_presconsumption) and
               (not delete_hydricmovements) and (not create_hydricmovements)):
                if 'adjustement_volume' in vals:
                    delete_hydricmovements = True
                    create_hydricmovements = True
            if delete_hydricmovements or create_hydricmovements:
                quota_model = self.env['wua.quota']
                if delete_hydricmovements:
                    quota_model.delete_hydricmovements_presconsumption(
                        updated_presconsumption)
                if create_hydricmovements:
                    quota_model.create_hydricmovements_presconsumption(
                        updated_presconsumption)
        return True

    # This funcion gets the pressurized consumptions of a water connection,
    # (type='waterconnection'), a irrigation shed (type='irrigationshed')
    # or a hydraulic sector (type='hydraulicsector'). If the
    # "active_agriculturalseason" parameter is True, the consumptions
    # will be from the active agricultural season.
    def get_presconsumptions(self, id, active_agriculturalseason,
                             type='waterconnection'):
        resp = []
        condition = [('waterconnection_id', '=', id)]
        if type == 'irrigationshed':
            condition = [('irrigationshed_id', '=', id)]
        if type == 'hydraulicsector':
            condition = [('hydraulicsector_id', '=', id)]
        agriculturalseason_ok = True
        if active_agriculturalseason:
            agriculturalseason = self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
            if agriculturalseason:
                condition.append(
                    ('agriculturalseason_id', '=', agriculturalseason.id))
            else:
                agriculturalseason_ok = False
        if agriculturalseason_ok:
            resp = self.search(condition, order='reading_end_time')
        return resp

    # Hook ("False" when the consumption is not validated)
    def is_valid_presconsumption(self, updated_presconsumption):
        resp = updated_presconsumption.validated
        return resp

    # Hook ("True" if changes the validation state). The first output
    # parameter indicates if something needs to be done (at least delete
    # the old hydric consumptions); the second output parameter indicates
    # if it is necessary to create the hydric consumptions again.
    def _force_refresh_hydricmovements(self, updated_presconsumption, vals):
        return False, False
