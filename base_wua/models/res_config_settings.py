# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    concessions_mandatory_default_parcels = fields.Boolean(
        string='Concessions: Set mandatory by default in parcels',
        config_parameter='base_wua.concessions_mandatory_default_parcels',
        help='If checked, the concession will be mandatory in parcels',
    )
