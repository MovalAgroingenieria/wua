# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    irrigationsrequest_id = fields.Many2one(
        string='Irrigations Request',
        comodel_name='wua.irrigationsrequest',
        index=True,
        ondelete='restrict',
        readonly=True)

    mapped_to_irrigationsrequest = fields.Boolean(
        string='Mapped to an irrigations request',
        store=True,
        compute='_compute_mapped_to_irrigationsrequest')

    @api.depends('irrigationsrequest_id')
    def _compute_mapped_to_irrigationsrequest(self):
        for record in self:
            mapped_to_irrigationsrequest = False
            if record.irrigationsrequest_id:
                mapped_to_irrigationsrequest = True
            record.mapped_to_irrigationsrequest = mapped_to_irrigationsrequest

    @api.multi
    def unlink(self):
        # If it comes from an irrigationsrequest that is being invalidated
        # Can be deleted
        is_resetting = self.env.context.get('resetting')
        if not is_resetting:
            for record in self:
                if record.mapped_to_irrigationsrequest:
                    raise exceptions.ValidationError(_(
                        'Cannot delete an irrigationreport associated to an '
                        'irrigationsrequest.'))
        return super(WuaIrrigationReport, self).unlink()
