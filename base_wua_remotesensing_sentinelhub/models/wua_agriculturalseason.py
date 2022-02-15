# -*- coding: utf-8 -*-
# 2022 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    @api.multi
    def write(self, vals):
        if (not (len(self) == 1 and 'active_agriculturalseason' in vals)):
            resp = super(WuaAgriculturalseason, self).write(vals)
        else:
            val_active_agriculturalseason = \
                vals['active_agriculturalseason']
            if val_active_agriculturalseason:
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                        UPDATE wua_agriculturalseason
                        SET active_agriculturalseason=FALSE WHERE
                        active_agriculturalseason=TRUE""")
                except Exception:
                    self.env.cr.rollback()
                    raise exceptions.UserError(_(
                        'Error when updating records '
                        '(\"of_active_agriculturalseason\" field).'))
            resp = super(WuaAgriculturalseason, self).write(vals)
        return resp

    @api.multi
    def action_activate_agriculturalseason(self):
        self.ensure_one()
        self.active_agriculturalseason = True

    @api.model
    def action_global_assignment(self):
        self.do_global_assignment()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }

    # Hook
    @api.model
    def do_global_assignment(self):
        # Here: execution of this method from daughter classes (assignment of
        # agricultural season for each measurement).
        # (execution in daughter classes -specializated modules-)
        # After... If there is a active agricultural season, populating the
        # "of_active_agriculturalseason" field, for all the measurements.
        current_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if current_agriculturalseason:
            current_agriculturalseason = current_agriculturalseason[0]
            current_agriculturalseason.active_agriculturalseason = True
