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
        string='Num. of files',
        compute='_compute_number_of_files')

    file_res_letter_ids = fields.One2many(
        string='File Registry',
        comodel_name='res.letter',
        inverse_name='file_id',
        compute='_compute_file_res_letter_ids')

    number_of_file_registers = fields.Integer(
        string='Num. file registers',
        compute='_compute_number_of_file_registers')

    @api.multi
    def _compute_number_of_files(self):
        for record in self:
            number_of_files = 0
            parcellinks_of_parcel = self.sudo().env['res.file.parcellink'].search(
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
            search_view = \
                self.env.ref('wua_crm_filemgmt.'
                             'res_file_parcellink_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('File Parcellinks'),
                'res_model': 'res.file.parcellink',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.file_ids.ids)],
                }
            return act_window

    @api.multi
    def _compute_number_of_file_registers(self):
        for record in self:
            record.number_of_file_registers = len(record.file_res_letter_ids)

    @api.multi
    def action_get_registers(self):
        self.ensure_one()
        if self.file_res_letter_ids:
            id_tree_view = self.env.ref('crm_lettermgmt.'
                                        'res_letter_tree_o2m_view').id
            id_form_view = self.env.ref('crm_lettermgmt.'
                                        'res_letter_form_view').id
            search_view = self.env.ref('crm_lettermgmt.res_letter_filter')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('File registers'),
                'res_model': 'res.letter',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'),
                          (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.file_res_letter_ids.ids)],
                }
            return act_window

    @api.depends('file_ids')
    def _compute_file_res_letter_ids(self):
        for record in self:
            parcel_file_ids = []
            registers_of_parcel = []
            if record.file_ids:
                for parcel_file_id in record.file_ids:
                    parcel_file_ids.append(parcel_file_id.file_id.id)
            if len(parcel_file_ids) > 0:
                registers_of_parcel = self.env['res.letter'].search(
                    [('file_id.id', 'in', parcel_file_ids)])
            if registers_of_parcel:
                record.file_res_letter_ids = registers_of_parcel
