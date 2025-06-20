from odoo import models, fields, api


class WuaTertiaryPipe(models.Model):
    _name = 'wua.tertiarypipe'
    _description = 'Tertiary Pipe'

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
    )

    code = fields.Char(
        string='Code',
        required=True,
        index=True,
    )

    waterconnection_id = fields.Many2one(
        comodel_name='wua.waterconnection',
        string='Water Connection',
        required=True,
        index=True,
    )

    irrigationshed_id = fields.Many2one(
        comodel_name='wua.irrigationshed',
        string='Irrigation Shed',
        compute='_compute_irrigationshed_id',
        store=True,
        index=True,
    )

    watermeter_id = fields.Many2one(
        comodel_name='wua.watermeter',
        string='Water Meter',
        compute='_compute_watermeter_id',
        store=True,
        index=True,
    )

    hydraulicsector_id = fields.Many2one(
        comodel_name='wua.hydraulicsector',
        string='Hydraulic Sector',
        compute='_compute_hydraulicsector_id',
        store=True,
        index=True,
    )

    technical_notes = fields.Html(
        string='Technical Notes',
    )
    general_notes = fields.Html(
        string='General Notes',
    )

    photo = fields.Binary(
        string='Photo',
    )

    material = fields.Char(
        string='Material',
    )

    diameter = fields.Float(
        string='Diameter',
        digits=(32, 2),
    )

    nominal_pressure = fields.Float(
        string='Nominal Pressure',
        digits=(32, 2),
    )

    description = fields.Char(
        string='Description',
    )

    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count',
        store=False,
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The name must be unique.'),
        ('code_unique', 'unique(code)', 'The code must be unique.'),
    ]

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for rec in self:
            rec.irrigationshed_id = rec.waterconnection_id.irrigationshed_id

    @api.depends('waterconnection_id')
    def _compute_watermeter_id(self):
        for rec in self:
            rec.watermeter_id = rec.waterconnection_id.watermeter_id

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for rec in self:
            rec.hydraulicsector_id = rec.waterconnection_id.hydraulicsector_id

    @api.depends('waterconnection_id')
    def _compute_parcel_count(self):
        for rec in self:
            rec.parcel_count = self.env['wua.parcel'].search_count([
                ('irrigationpoint_ids.waterconnection_id.id', '=',
                 rec.waterconnection_id.id),
            ])

    def action_view_supplied_parcels(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplied Parcels',
            'res_model': 'wua.parcel',
            'view_mode': 'tree,form',
            'domain': [
                ('irrigationpoint_ids.waterconnection_id.id', '=',
                 self.waterconnection_id.id)],
            'context': {
                'default_waterconnection_id': self.waterconnection_id.id},
        }
