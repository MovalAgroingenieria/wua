# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationgate(models.Model):
    _inherit = 'wua.irrigationgate'

    main_irrigationditch_id = fields.Many2one(
        string="Main irrigation ditch",
        comodel_name="wua.irrigationditch",
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_main_irrigationditch_id')

    @api.depends('irrigationditch_id', 'irrigationditch_id.path')
    def _compute_main_irrigationditch_id(self):
        for record in self:
            main_irrigationditch_id = None
            if (record.irrigationditch_id and
               record.irrigationditch_id.main_irrigationditch_id):
                main_irrigationditch_id = \
                    record.irrigationditch_id.main_irrigationditch_id.id
            record.main_irrigationditch_id = main_irrigationditch_id
