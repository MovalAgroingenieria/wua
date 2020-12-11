# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'

    @api.model
    def create(self, vals):
        has_notes = ""
        if 'gravconsumption_ids' in vals and 'notes' in vals:
            has_gravconsumptions = vals.get('gravconsumption_ids')
            has_notes = vals.get('notes')
        if has_notes and has_gravconsumptions:
            gravconsumption_ids = vals['gravconsumption_ids']
            grav_vals = _('<b>Notes from watering request:</b>') + \
                vals['notes']
            for gravconsumption in gravconsumption_ids:
                gravconsumption[2]['notes'] = grav_vals
        return super(WuaWateringrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        has_notes = ""
        if 'notes' in vals:
            has_notes = vals.get('notes')
            if has_notes:
                grav_vals = _('<b>Notes from watering request:</b>') + \
                    vals['notes']
            if 'gravconsumption_ids' in vals:
                has_gravconsumptions = vals.get('gravconsumption_ids')
                if has_gravconsumptions:
                    gravconsumption_ids = vals['gravconsumption_ids']
                    for gravconsumption in gravconsumption_ids:
                        if gravconsumption[2]:
                            gravconsumption[2]['notes'] = grav_vals
            else:
                gravconsumption_ids = \
                    self.env['wua.gravconsumption'].search(
                        [('wateringrequest_id', '=', self.id)])
                for gravconsumption in gravconsumption_ids:
                    gravconsumption.notes = grav_vals
        return super(WuaWateringrequest, self).write(vals)
