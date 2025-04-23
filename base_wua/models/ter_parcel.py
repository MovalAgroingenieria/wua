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
