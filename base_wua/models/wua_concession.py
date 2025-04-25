# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api


class WuaConcession(models.Model):
    _name = 'wua.concession'
    _description = 'Water Concession'
    _inherit = ['simple.model', ]

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 50
    _minlength = 0
    _maxlength = 50
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 100

    # Fields
    alphanum_code = fields.Char(
        string='Short Name',
        required=True,
    )

    description = fields.Char(
        string='Long Name / Description',
        translate=True,
    )

    annual_volume = fields.Integer(
        string='Annual Volume (m³)',
        default=0,
        required=True,
        index=True,
    )

    area = fields.Integer(
        string='Area (ha)',
        default=0,
        required=True,
        index=True,
    )

    associated_file = fields.Char(
        string='File Code',
        index=True,
    )

    flow = fields.Float(
        string='Flow (l/s)',
        digits=(32, 2),
        default=0,
        required=True,
        index=True,
    )

    provision = fields.Float(
        string='Provision (m³/ha)',
        digits=(32, 2),
        store=True,
        index=True,
        compute='_compute_provision',
    )

    concessionlink_ids = fields.One2many(
        string='Concessions in parcels',
        comodel_name='ter.parcel.concessionlink',
        inverse_name='parcel_id',
    )

    _sql_constraints = [
        ('annual_volume_ok', 'CHECK (annual_volume >= 0)',
         'Incorrect value for "Annual Volume (m³)".'),
        ('area_ok', 'CHECK (area >= 0)', 'Incorrect value for "Area (ha)".'),
        ('flow_ok', 'CHECK (flow >= 0)', 'Incorrect value for "Flow (l/s)".'),
    ]

    @api.depends('annual_volume', 'area')
    def _compute_provision(self):
        for record in self:
            if record.area > 0:
                record.provision = record.annual_volume / record.area
            else:
                record.provision = 0
