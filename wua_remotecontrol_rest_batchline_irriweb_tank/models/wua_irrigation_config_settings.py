# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    import_from_tankconsumptions = fields.Boolean(
        string='Import from tankconsumptions')

    php_frame_type_solicitudcuba = fields.Char(
        string='PHP (frames), tank scheduling',
        size=50,
        help='For build a PHP url that gives the scheduling of tanks. ' +
             'Example: http://78.136.122.3:8080/demo/baja/solicitudcuba.php')

    php_frame_type_solicitudcuba_width = fields.Integer(
        string='PHP (frames), tank scheduling width')

    php_frame_type_solicitudcuba_height = fields.Integer(
        string='PHP (frames), tank scheduling height')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'import_from_tankconsumptions',
                           self.import_from_tankconsumptions)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_solicitudcuba',
                           self.php_frame_type_solicitudcuba)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_solicitudcuba_width',
                           self.php_frame_type_solicitudcuba_width)
        values.set_default('wua.irrigation.configuration',
                           'php_frame_type_solicitudcuba_height',
                           self.php_frame_type_solicitudcuba_height)
