# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _, exceptions


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    _in_create = False

    telecontrol_associated = fields.Selection(
        selection_add=[('batchline', 'Batchline')],)

    html_readings_frame = fields.Text(
        string='IrriWEB Readings',
        compute='_compute_html_readings_frame'
        )

    html_consumptions_frame = fields.Text(
        string='IrriWEB Consumptions',
        compute='_compute_html_consumptions_frame'
        )

    html_scheduling_frame = fields.Text(
        string='IrriWEB Scheduling',
        compute='_compute_html_scheduling_frame'
        )

    @api.multi
    def _compute_html_readings_frame(self):
        if self.__class__._in_create:
            self.__class__._in_create = False
            return
        url_ok, url, width, height = self.sudo()._get_url_frame('historico')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().irrigationshed_id.name
                toma_param = str(record.sudo().position)
                clientidentify_param = self.env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_readings_frame = \
                    '<p style="text-align:center;margin-top:2px;' + \
                    'margin-left:1px;margin-right:1px; overflow: auto;">' + \
                    '<iframe sandbox="allow-scripts allow-forms ' + \
                    'allow-pointer-lock allow-same-origin" ' + \
                    'id="iframe_readings" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'loading=lazy src="' + url + '" ' + \
                    'frameborder="0" height="' + str(height) + '" ' + \
                    'width="' + str(width) + '"' + \
                    '></iframe></p>'
            else:
                record.html_readings_frame = ''

    @api.multi
    def _compute_html_consumptions_frame(self):
        url_ok, url, width, height = self.sudo()._get_url_frame('consumo')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().irrigationshed_id.name
                toma_param = str(record.sudo().position)
                clientidentify_param = self.env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_consumptions_frame = \
                    '<p style="text-align:center;margin-top:2px;' + \
                    'margin-left:1px;margin-right:1px; overflow: auto;">' + \
                    '<iframe sandbox="allow-scripts allow-forms ' + \
                    'allow-pointer-lock allow-same-origin" ' + \
                    'id="iframe_consumptions" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'loading=lazy src="' + url + '" ' + \
                    'frameborder="0" height="' + str(height) + '" ' + \
                    'width="' + str(width) + '"' + \
                    '></iframe></p>'
            else:
                record.html_consumptions_frame = ''

    @api.multi
    def _compute_html_scheduling_frame(self):
        url_ok, url, width, height = self.sudo()._get_url_frame('programacion')
        for record in self:
            if url_ok:
                hidrante_param = record.sudo().irrigationshed_id.name
                toma_param = str(record.sudo().position)
                clientidentify_param = self.env.user.name
                url = url + '&hidrante=' + hidrante_param + '&' + \
                    'toma=' + toma_param + '&' + \
                    'clientidentify=' + clientidentify_param
                record.html_scheduling_frame = \
                    '<p style="text-align:center;margin-top:2px;' + \
                    'margin-left:1px;margin-right:1px; overflow: auto;">' + \
                    '<iframe sandbox="allow-scripts allow-forms ' + \
                    'allow-pointer-lock allow-same-origin ' + \
                    'allow-modals" ' + \
                    'id="iframe_scheduling" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="0" height="' + str(height) + '" ' + \
                    'width="' + str(width) + '"' + \
                    '></iframe></p>'
            else:
                record.html_scheduling_frame = ''

    @api.model
    def create(self, vals):
        waterconnection = super(WuaWaterconnection, self).create(vals)
        self.__class__._in_create = True
        return waterconnection

    @api.multi
    def action_scheduling_waterconnection(self):
        self.ensure_one()
        is_portal_user = self.env.user.has_group(
            'base_wua.group_wua_portal_user')
        current_partner_id = self.env.user.partner_id
        if (is_portal_user and self.id not in
                (current_partner_id.waterconnectionlink_ids.mapped(
                lambda x: x.waterconnection_id.id) +
                current_partner_id.parent_id.waterconnectionlink_ids.mapped(
                lambda x: x.waterconnection_id.id))):
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.error(
                'Partner ' + current_partner_id.name + ' is not the owner ' +
                'of ' + self.name)
            raise exceptions.UserError(_(
                'You are not the owner of the waterconnection'))
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Schedule water connection'),
            'res_model': 'wizard.scheduling.waterconnection',
            'src_model': 'wua.waterconnection',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    def _get_url_frame(self, type):
        url_ok = False
        url = ''
        width = 0
        height = 0
        php_frame_enabled = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_enabled')
        php_frame_url = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'php_frame_url')
        url_irriweb = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_batchline')
        url_ok = php_frame_enabled and php_frame_url and url_irriweb
        if url_ok:
            if type == 'historico':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_historico')
                width = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_historico_width')
                height = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_historico_height')
            if type == 'consumo':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_consumo')
                width = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_consumo_width')
                height = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_consumo_height')
            if type == 'programacion':
                php_frame_type = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_programacion')
                width = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_programacion_width')
                height = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'php_frame_type_programacion_height')
            php_frame_client = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_client')
            php_frame_accesskey = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_accesskey')
            php_frame_secretkey = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'php_frame_secretkey')
            url = php_frame_url + '?type=' + php_frame_type + \
                '&url_irriweb=' + url_irriweb + \
                '&client=' + php_frame_client + \
                '&accesskey=' + php_frame_accesskey + \
                '&secretkey=' + php_frame_secretkey + \
                '&height=' + str(height) + \
                '&width=' + str(width)
        return url_ok, url, width, height
