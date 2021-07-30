# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    number_of_certificates = fields.Integer(
        string='Number of certificates',
        compute_sudo=True,
        compute='_compute_number_of_certificates')

    can_request_certificate = fields.Boolean(
        string='It is possible to request a certificate',
        compute_sudo=True,
        compute='_compute_can_request_certificate')

    @api.multi
    def _compute_number_of_certificates(self):
        model_wua_certificate = self.env['wua.certificate']
        for record in self:
            number_of_certificates = 0
            certificates = model_wua_certificate.search(
                [('partner_id', '=', record.id)])
            if certificates:
                number_of_certificates = len(certificates)
            record.number_of_certificates = number_of_certificates

    @api.multi
    def _compute_can_request_certificate(self):
        is_portal_user = self.env.user.has_group(
            'base_wua.group_wua_portal_user')
        for record in self:
            can_request_certificate = True
            if is_portal_user:
                allowed_request_for_portal_user = \
                    self.env['ir.values'].get_default(
                        'wua.configuration', 'allowed_request_for_portal_user')
                can_request_certificate = allowed_request_for_portal_user
            record.can_request_certificate = can_request_certificate

    @api.multi
    def name_get(self):
        if self.env.context.get('show_only_partner_code', False):
            result = []
            for record in self:
                result.append((record.id, str(record.partner_code)))
        else:
            result = super(ResPartner, self).name_get()
        return result

    @api.multi
    def action_get_certificates(self):
        self.ensure_one()
        if self.number_of_certificates > 0:
            id_tree_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_one_partner_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_display_view_form').id
            search_view = self.env.ref(
                'base_wua_certificate.'
                'wua_certificate_one_partner_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Certificates'),
                'res_model': 'wua.certificate',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('partner_id', '=', self.id)],
                'context': {'show_only_partner_code': True},
                }
            return act_window

    @api.multi
    def action_create_certificate(self):
        self.ensure_one()
        num_pending_certificates = 0
        max_pending_certificates = self._get_max_pending_certificates()
        pending_certificates = self.env['wua.certificate'].search(
            [('partner_id', '=', self.id), ('state', '=', '01_draft')])
        if pending_certificates:
            num_pending_certificates = len(pending_certificates)
        if num_pending_certificates >= max_pending_certificates:
            raise exceptions.UserError(
                _('Maximum number of certificates pending validation '
                  'exceeded') + ' (' + str(max_pending_certificates) + ').')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Create a certificate'),
            'res_model': 'wizard.create.certificate',
            'src_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    def _get_max_pending_certificates(self):
        resp = 0
        max_pending_certificates = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'max_pending_certificates')
        if max_pending_certificates:
            resp = max_pending_certificates
        return resp
