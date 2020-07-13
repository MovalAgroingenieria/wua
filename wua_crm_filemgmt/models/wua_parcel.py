# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    file_ids = fields.One2many(
        string='Associated Files',
        comodel_name='res.file.parcellink',
        inverse_name='parcel_id')

    number_of_files = fields.Integer(
        string='Files',
        compute='_compute_number_of_files')

    @api.multi
    def _compute_number_of_files(self):
        for record in self:
            number_of_files = 0
            parcellinks_of_parcel = self.env['res.file.parcellink'].search(
                [('parcel_id', '=', record.id)])
            if parcellinks_of_parcel:
                number_of_files = len(parcellinks_of_parcel)
            record.number_of_files = number_of_files

    @api.multi
    def action_get_files(self):
        self.ensure_one()
        if self.file_ids:
            id_tree_view = \
                self.env.ref('wua_crm_filemgmt.'
                             'res_file_parcellink_of_parcel_view_tree').id
            id_form_view = \
                self.env.ref('wua_crm_filemgmt.'
                             'res_file_parcellink_view_form').id
            search_view = \
                self.env.ref('wua_crm_filemgmt.'
                             'res_file_parcellink_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('File Parcellinks'),
                'res_model': 'res.file.parcellink',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'),
                          (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.file_ids.ids)],
                }
            return act_window
