# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    show_sign = fields.Boolean(
        string='Show signature in PDF',
        default=True,
        help='Activate this parameter to show the signature data '
             'in the signed PDF')

    page_of_signature = fields.Integer(
        string='Signature Page',
        default=1,
        help='If the page of signature is the last one, then enter a hight '
             'value (1000, by example)')

    llx_for_signature = fields.Integer(
        string='Lower Left X',
        default=30,
        help='From bottom left corner of paper, X-distance of the lower left '
             'point of signature frame')

    lly_for_signature = fields.Integer(
        string='Lower Left Y',
        default=70,
        help='From bottom left corner of paper, Y-distance of the lower left '
             'point of signature frame')

    urx_for_signature = fields.Integer(
        string='Upper right X',
        default=225,
        help='From bottom left corner of paper, X-distance of the upper right '
             'point of signature frame')

    ury_for_signature = fields.Integer(
        string='Upper right Y',
        default=193,
        help='From bottom left corner of paper, Y-distance of the upper right '
             'point of signature frame')

    max_signatures = fields.Integer(
        string='N. of signatures',
        default=2,
        help='Maximum number of printed signatures (internally there is no '
             'maximum value)')

    column_spacing = fields.Integer(
        string='Column Spacing',
        default=110,
        help='Distance between two printed signatures')

    fit_image = fields.Boolean(
        string='Fit image',
        default=True,
        help='If there is a background image, fitting this image to available '
             'frame')

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.configuration', 'show_sign',
                           self.show_sign)
        values.set_default('wua.configuration', 'page_of_signature',
                           self.page_of_signature)
        values.set_default('wua.configuration', 'llx_for_signature',
                           self.llx_for_signature)
        values.set_default('wua.configuration', 'lly_for_signature',
                           self.lly_for_signature)
        values.set_default('wua.configuration', 'urx_for_signature',
                           self.urx_for_signature)
        values.set_default('wua.configuration', 'ury_for_signature',
                           self.ury_for_signature)
        values.set_default('wua.configuration', 'max_signatures',
                           self.max_signatures)
        values.set_default('wua.configuration', 'column_spacing',
                           self.column_spacing)
        values.set_default('wua.configuration', 'fit_image',
                           self.fit_image)
