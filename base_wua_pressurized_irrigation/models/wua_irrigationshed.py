from odoo import models, fields


class WuaIrrigationShed(models.Model):
    _inherit = 'wua.irrigationshed'

    zone_id = fields.Many2one(
        string='Zone',
        comodel_name='wua.zone',
        index=True,
        store=True,
    )
