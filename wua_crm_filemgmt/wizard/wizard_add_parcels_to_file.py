# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardAddParcelsFile(models.TransientModel):
    _name = 'wizard.add.parcels.file'

    def _default_file_code(self):
        file_code = self.env['res.file']._default_file_code()
        return file_code

    def _default_category_id(self):
        proposed_category = self.env['res.file']._default_category_id()
        return proposed_category

    def _default_selected_parcels(self):
        selected_parcels_list = []
        for active_id in self.env.context['active_ids']:
            parcel = self.env['wua.parcel'].browse(active_id)
            selected_parcels_list.append(parcel.name)
        selected_parcels_set = list(set(selected_parcels_list))
        selected_parcels = '\n'.join(selected_parcels_set)
        return selected_parcels

    def _default_selected_partners(self):
        selected_partners_list = []
        for active_id in self.env.context['active_ids']:
            parcel = self.env['wua.parcel'].browse(active_id)
            for partnerlink in parcel.partnerlink_ids:
                partner_name = partnerlink.partner_id.display_name
                partner_profile = dict(
                    self.env['wua.parcel.partnerlink'].fields_get(
                        allfields=['profile'])['profile']['selection'])[
                            partnerlink.profile]
                partner = partner_name + ' [' + partner_profile + ']'
                selected_partners_list.append(partner)
        selected_partners_set = list(set(selected_partners_list))
        selected_partners = '\n'.join(selected_partners_set)
        return selected_partners

    file_code = fields.Char(
        string='Code',
        size=30,
        default=_default_file_code,
        required=True)

    subject = fields.Char(
        string='Subject',
        size=150,
        required=True)

    category_id = fields.Many2one(
        string='Category',
        comodel_name='res.file.category',
        required=True,
        default=_default_category_id)

    date_file = fields.Date(
        string='Discharge date',
        default=lambda self: fields.datetime.now(),
        required=True)

    selected_parcels = fields.Text(
        string="Selected parcels",
        default=_default_selected_parcels,
        compute="_compute_selected_parcels")

    selected_partners = fields.Text(
        string="Selected partners",
        default=_default_selected_partners,
        compute="_compute_selected_partners")

    @api.multi
    def _compute_selected_parcels(self):
        for record in self:
            parcel_ids_list = []
            for active_id in record.env.context['active_ids']:
                parcel_ids_list.append(active_id)
            parcel_ids = list(set(parcel_ids_list))
            record.selected_parcels = parcel_ids

    @api.multi
    def _compute_selected_partners(self):
        for record in self:
            partner_ids_list = []
            for active_id in record.env.context['active_ids']:
                parcel = self.env['wua.parcel'].browse(active_id)
                for partnerlink in parcel.partnerlink_ids:
                    partner_id = partnerlink.partner_id.id
                    partner_ids_list.append(partner_id)
            partner_ids = list(set(partner_ids_list))
            record.selected_partners = partner_ids

    def create_file(self):
        self.ensure_one()
        partner_ids = eval(self.selected_partners)
        partner_ids_data = []
        is_main = True
        for partner_id in partner_ids:
            partnerlink_data = \
                (0, 0, {'partner_id': partner_id, 'is_main': is_main})
            partner_ids_data.append(partnerlink_data)
            is_main = False
        parcel_ids = eval(self.selected_parcels)
        parcel_ids_data = []
        for parcel_id in parcel_ids:
            parcellink_data = (0, 0, {'parcel_id': parcel_id})
            parcel_ids_data.append(parcellink_data)
        vals = {
            'name': self.file_code,
            'subject': self.subject,
            'category_id': self.category_id.id,
            'date_file': self.date_file,
            'partnerlink_ids': partner_ids_data,
            'parcellink_ids': parcel_ids_data
        }
        new_file = self.env['res.file'].create(vals)
        view_id = self.env.ref('crm_filemgmt.res_file_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('File'),
            'res_model': 'res.file',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'view_id': view_id.id,
            'res_id': new_file.id,
        }
        return act_window
