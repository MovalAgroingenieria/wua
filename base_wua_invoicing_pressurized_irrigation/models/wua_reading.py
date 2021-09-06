# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _description = 'Entity (pressure reading)'

    invoiced_reading = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced_reading')

    @api.depends('presconsumption_id',
                 'presconsumption_id.invoiced_consumption')
    def _compute_invoiced_reading(self):
        for record in self:
            invoiced_reading = False
            if record.presconsumption_id:
                invoiced_reading = \
                    record.presconsumption_id.invoiced_consumption
            record.invoiced_reading = invoiced_reading

    @api.multi
    def unlink(self):
        for record in self:
            if (record.invoiced_reading):
                raise exceptions.UserError(
                    _('Cannot delete reading with invoiced consumptions.'))
        return super(WuaReading, self).unlink()

    @api.multi
    def write(self, vals):
        readonly_values_when_invoiced = ['volume', 'validated']
        for record in self:
            # Check if any of trigger values appears and then check if is an
            # already invoiced reading
            if (any([i in vals for i in readonly_values_when_invoiced])):
                if (record.invoiced_reading):
                    raise exceptions.UserError(
                        _('Cannot update reading with invoiced consumptions.'))
        # Call inherited write operation.
        return super(WuaReading, self).write(vals)
