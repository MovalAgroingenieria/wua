# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _


class WuaInfrastructureitem(models.AbstractModel):
    _name = 'wua.infrastructureitem'
    _description = 'Infrastructure Item (abstract model)'

    equipment_id = fields.Many2one(
        string='Equipment',
        comodel_name='maintenance.equipment',
        ondelete='cascade',
    )

    active = fields.Boolean(
        default=True,
    )

    @api.model
    def create(self, vals):
        equipment = None
        equipment_vals = self._get_equipment_vals_for_create(vals)
        if equipment_vals:
            equipment = self.env['maintenance.equipment'].create(
                equipment_vals)
        item = super(WuaInfrastructureitem, self).create(vals)
        if equipment is not None:
            item.equipment_id = equipment
        return item

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            equipment = self.equipment_id
            equipment_vals = self._get_equipment_vals_for_write(vals)
            if equipment_vals:
                equipment.write(equipment_vals)
            if 'active' in vals:
                if not self.env.context.get('update_from_equipment', False):
                    for record in self:
                        record.equipment_id.with_context(
                            {'update_from_infrastructure': True}).write(
                            {'active': vals['active']})

        return super(WuaInfrastructureitem, self).write(vals)

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        # Specialized code (hook)
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        # Specialized code (hook)
        return vals

    def action_get_equipment(self):
        if not self.equipment_id:
            raise exceptions.UserError(_('Equipment not available.'))
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Equipment'),
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'res_id': self.equipment_id.id,
            'context': {
                'create': False,
            },
        }
        return act_window

    @api.multi
    def unlink(self):
        for record in self:
            if record and record.equipment_id:
                record.equipment_id.unlink()
        res = super(WuaInfrastructureitem, self).unlink()
        return res
