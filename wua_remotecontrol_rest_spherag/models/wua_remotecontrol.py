# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class WuaRemotecontrol(models.Model):
    _inherit = 'wua.remotecontrol'

    def _build_spherag_import_message(self, bag):
        result = bag.get('wua_import_result') or {}
        attachment_name = bag.get('attachment_name') or ''
        message = _(
            'Spherag import finished. Created sheds: %(sheds)s, '
            'created waterconnections: %(wcs)s, created watermeters: %(wms)s, '
            'updated waterconnections: %(updates)s, '
            'skipped elements: %(skip)s.'
        ) % {
            'sheds': result.get('created_irrigationsheds', 0),
            'wcs': result.get('created_waterconnections', 0),
            'wms': result.get('created_watermeters', 0),
            'updates': result.get('updated_waterconnections', 0),
            'skip': result.get('skipped_elements', 0),
        }
        if attachment_name:
            message += _(' Discovery file: %s.') % attachment_name
        return message

    def action_import_spherag_infrastructure(self):
        self.ensure_one()
        procedure = self.env.ref(
            'wua_remotecontrol_rest_spherag.'
            'remotecontrol_spherag_wua_procedure_import_infrastructure')
        bag = procedure._prepare_procedure_bag()
        for step in procedure.step_ids.sorted(key=lambda s: s.sequence):
            bag = step.action_id.execute(bag=bag)
        message = self._build_spherag_import_message(bag)
        self.message_post(body=message)
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Spherag Import'),
            'message': message,
            'is_html_message': False,
            'close_button_title': False,
            'buttons': [{
                'type': 'ir.actions.act_window_close',
                'name': _('Close'),
            }],
        }
