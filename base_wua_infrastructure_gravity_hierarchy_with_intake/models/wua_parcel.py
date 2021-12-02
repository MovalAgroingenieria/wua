from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    intake_id = fields.Many2one(
        string="Intake",
        comodel_name='wua.intake',
        index=True,
        store=True,
        compute="_compute_intake_id")

    @api.depends('irrigationditch_01_id', 'irrigationditch_01_id.intake_id')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if (record.irrigationditch_01_id and
                    record.irrigationditch_01_id.intake_id):
                intake_id = record.irrigationditch_01_id.intake_id
            record.intake_id = intake_id
