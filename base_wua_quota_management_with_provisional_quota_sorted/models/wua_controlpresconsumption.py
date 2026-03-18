# -*- coding: utf-8 -*-
# 2023 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaControlpresconsumption(models.Model):
    _inherit = 'wua.controlpresconsumption'

    controlhydricmovement_ids = fields.One2many(
        string='Control Hydric-Movements',
        comodel_name='wua.controlhydricmovement',
        inverse_name='controlpresconsumption_id')

    # This method is reimplemented because in the create method is not
    # available the waterconnection_id field. This computed method is called
    # after the create method.
    def _compute_hydraulic_infrastructure_data(self):
        # Save the set of records being created BEFORE calling super,
        # because super (provisional_quota module) will discard the ids
        # from the set when it processes them.
        creating_cps = getattr(self.env.all, '_creating_cps', None)
        records_creating = set()
        if creating_cps:
            records_creating = set(
                r.id for r in self if r.id in creating_cps)
        super(WuaControlpresconsumption,
              self)._compute_hydraulic_infrastructure_data()
        if records_creating:
            quota_model = self.env['wua.quota']
            for record in self:
                if (record.id in records_creating and
                        self.is_valid_controlpresconsumption(record)):
                    quota_model.create_controlhydricmovements_presconsumption(
                        record)

    def write(self, vals):
        super(WuaControlpresconsumption, self).write(vals)
        if len(self) == 1:
            updated_controlpresconsumption = self
            delete_controlhydricmovements, create_controlhydricmovements = \
                self._force_refresh_controlhydricmovements(
                    updated_controlpresconsumption, vals)
            # It is not possible to create hydric movements and not
            # eliminate previous movements.
            if (create_controlhydricmovements and
               (not delete_controlhydricmovements)):
                create_controlhydricmovements = False
            if (self.is_valid_controlpresconsumption(updated_controlpresconsumption) and
               (not delete_controlhydricmovements) and
               (not create_controlhydricmovements)):
                if 'adjustement_volume' in vals:
                    delete_controlhydricmovements = True
                    create_controlhydricmovements = True
            if delete_controlhydricmovements or create_controlhydricmovements:
                quota_model = self.env['wua.quota']
                if delete_controlhydricmovements:
                    quota_model.delete_controlhydricmovements_presconsumption(
                        updated_controlpresconsumption)
                if create_controlhydricmovements:
                    quota_model.create_controlhydricmovements_presconsumption(
                        updated_controlpresconsumption)
        return True

    # Hook ("False" when the control consumption is not validated)
    def is_valid_controlpresconsumption(self, updated_controlpresconsumption):
        resp = updated_controlpresconsumption.validated
        return resp

    # Hook ("True" if changes the validation state). The first output
    # parameter indicates if something needs to be done (at least delete
    # the old hydric consumptions); the second output parameter indicates
    # if it is necessary to create the hydric consumptions again.
    def _force_refresh_controlhydricmovements(
            self, updated_controlpresconsumption, vals):
        return False, False
