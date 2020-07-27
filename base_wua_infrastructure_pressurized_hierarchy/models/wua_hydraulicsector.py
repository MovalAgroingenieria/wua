# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'

    waterpipe_ids = fields.One2many(
        string='Water pipes',
        comodel_name='wua.waterpipe',
        inverse_name='hydraulicsector_id')

    main_waterpipe_id = fields.Many2one(
        string='Main Water Pipe',
        comodel_name='wua.waterpipe',
        store=True,
        compute='_compute_main_waterpipe_id')

    @api.depends('waterpipe_ids')
    def _compute_main_waterpipe_id(self):
        for record in self:
            main_waterpipe_id = None
            if record.waterpipe_ids:
                for waterpipe in record.waterpipe_ids:
                    if waterpipe.is_main:
                        main_waterpipe_id = waterpipe
                        break
            record.main_waterpipe_id = main_waterpipe_id

    @api.constrains('waterpipe_ids')
    def _check_waterpipe_ids(self):
        if len(self) == 1:
            found_main = False
            for waterpipe in (self.waterpipe_ids or []):
                if waterpipe.is_main:
                    if not found_main:
                        found_main = True
                    else:
                        raise exceptions.ValidationError(
                            _('The associated hydraulic sector already has a '
                              'main water-pipe.'))
