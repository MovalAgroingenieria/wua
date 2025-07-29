from odoo import models, fields, api


class WuaTertiaryPipe(models.Model):
    _name = 'wua.tertiarypipe'
    _description = 'Tertiary Pipe'

    name = fields.Char(
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
        string='Diameter (mm)',
        digits=(32, 2),
    )

    nominal_pressure = fields.Float(
        string='Nominal Pressure (bar)',
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

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    with_gis_tertiarypipe = fields.Boolean(
        string='GIS Tertiary Pipe',
    )

    _sql_constraints = [
        ('code_unique', 'unique(name)', 'The code must be unique.'),
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

    @api.depends('name')
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        tertiarypipe_param = "tertiarypipeid"
        for record in self:
            url_for_record = url
            if url_for_record:
                if tertiarypipe_param:
                    sep_char = '?'
                    if '?' in url_for_record:
                        sep_char = '&'
                    url_for_record = "{}{}{}={}".format(url_for_record,
                                                        sep_char,
                                                        tertiarypipe_param,
                                                        record.name)
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if cipher_text:
                    sep_char = '?' if '?' not in url_for_record else '&'
                    url_for_record = "{}{}arg={}".format(url_for_record,
                                                         sep_char,
                                                         cipher_text)
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_tertiarypipe_table()
            parcel_model.create_tertiarypipe_triggers()
        except Exception:
            pass
