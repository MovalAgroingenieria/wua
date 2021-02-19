# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, exceptions, _


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    @api.constrains('flowmeter_id')
    def _check_flowmeter_id(self):
        if len(self) == 1:
            current_intake = self
            if current_intake.flowmeter_id:
                current_flowmeter = current_intake.flowmeter_id
                # The flow-meter for this intake ("current_flowmeter") cannot
                # be assigned to another intake.
                # Provisional
                other_intakes_of_flowmeter = self.env['wua.intake'].search(
                    [('id', '!=', current_intake.id),
                     ('flowmeter_id', '=', current_flowmeter.id)])
                if other_intakes_of_flowmeter:
                    raise exceptions.ValidationError(
                        _('Flowmeter already on intake.'))
                other_waterpipes_of_flowmeter = self.env['wua.waterpipe'].\
                    search(
                    [('flowmeter_id', '=', current_flowmeter.id)])
                if other_waterpipes_of_flowmeter:
                    raise exceptions.ValidationError(
                        _('Flowmeter already on waterpipe.'))
