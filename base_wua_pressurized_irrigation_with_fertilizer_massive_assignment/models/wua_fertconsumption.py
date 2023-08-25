# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFertconsumption(models.Model):
    _inherit = 'wua.fertconsumption'

    validated = fields.Boolean(
        string='Validated Fertconsumption',
        default=True,
        required=True,
    )

    fertconsumptionset_id = fields.Many2one(
        string='Fertconsumption Set',
        comodel_name='wua.fertconsumptionset',
        ondelete='set null',
        readonly=True,
    )

    @api.multi
    def validate_fertconsumption(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_fertconsumption(self):
        self.ensure_one()
        if not self.invoiced_consumption:
            self.validated = False
        else:
            raise exceptions.UserError(
                _('The fertconsumption is invoiced: it is not '
                  'possible to cancel it.'))

    def validate_fertconsumptions(self, active_fertconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        fertconsumptions = self.env['wua.fertconsumption'].browse(
            active_fertconsumptions)
        for fertconsumption in fertconsumptions:
            if not fertconsumption.validated:
                fertconsumption.validate_fertconsumption()

    def cancel_fertconsumptions(self, active_fertconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        fertconsumptions = self.env['wua.fertconsumption'].browse(
            active_fertconsumptions)
        for fertconsumption in fertconsumptions:
            if fertconsumption.validated:
                fertconsumption.cancel_fertconsumption()

    @api.multi
    def unlink(self):
        for record in self:
            if (record.fertconsumptionset_id and not self.env.context.get(
                    'force_unlink', False)):
                raise exceptions.UserError(_(
                    'You cannot delete a fertconsumption related with a '
                    'fertconsumption set, cancel it instead.'))
        return super(WuaFertconsumption, self).unlink()
