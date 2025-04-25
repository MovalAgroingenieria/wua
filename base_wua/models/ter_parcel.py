# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class TerParcelWua(models.Model):
    _inherit = 'ter.parcel'

    def _default_mandatory_concessions(self):
        config = self.env['ir.config_parameter'].sudo()
        mandatory_concessions = config.get_param(
            'base_wua.concessions_mandatory_default_parcels', False)
        return mandatory_concessions

    mandatory_concessions = fields.Boolean(
        string='Mandatory Concessions',
        default=_default_mandatory_concessions,
    )

    concessionlink_ids = fields.One2many(
        string='Concessions in parcels',
        comodel_name='ter.parcel.concessionlink',
        inverse_name='parcel_id',
    )

    @api.constrains('mandatory_concessions', 'concessionlink_ids')
    def _check_mandatory_concessions(self):
        for record in self:
            num_concessionlink_ids = len(record.concessionlink_ids)
            if record.mandatory_concessions and num_concessionlink_ids == 0:
                raise exceptions.ValidationError(
                    _('There are no concessions associated with the parcel, '
                      'and have been established as mandatory.'))


class TerParcelConcessionlink(models.Model):
    _name = 'ter.parcel.concessionlink'
    _description = 'Concession of parcel'

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='ter.parcel',
        required=True,
        ondelete='cascade',
    )

    concession_id = fields.Many2one(
        string='Concession',
        comodel_name='wua.concession',
        required=True,
    )

    name = fields.Char(
        string='Concessionlink',
        store=True,
        index=True,
        compute='_compute_name',
    )

    notes = fields.Char(
        string='Notes',
    )

    concession_description = fields.Char(
        string='Description',
        related='concession_id.description',
    )

    concession_provision = fields.Float(
        string='Provision (m³/ha)',
        digits=(32, 2),
        related='concession_id.provision',
    )

    active = fields.Boolean(
        store=True,
        related='parcel_id.active',)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (parcel_id, concession_id)',
         'Existing Concession.'),
    ]

    @api.depends('parcel_id', 'parcel_id.alphanum_code',
                 'concession_id', 'concession_id.alphanum_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.parcel_id:
                name += record.parcel_id.alphanum_code
            if record.concession_id:
                name += '-' + record.concession_id.alphanum_code
            record.name = name
