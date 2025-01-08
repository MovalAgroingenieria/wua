# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
import json
import base64


class WizardImportRemotecontrolData(models.TransientModel):
    _name = 'wizard.import.remotecontrol.data'
    _description = 'Wizard to Import Remote Control Data'

    remotecontrol_type = fields.Selection(
        string='Remote Control',
        selection=[],
        required=True,
    )

    element_to_import = fields.Selection(
        string='Element to Import',
        selection=[('reading', 'Reading')],
        required=True,
    )

    json_file = fields.Binary(
        string='JSON File',
        required=True,
    )

    json_file_name = fields.Char(
        string='File Name',
    )

    date = fields.Datetime(
        string='Date',
        required=True,
    )

    @api.multi
    def import_remote_data(self):
        self.ensure_one()
        try:
            decoded_json = base64.b64decode(self.json_file)
            data = json.loads(decoded_json)
        except Exception as e:
            raise exceptions.UserError(
                _("The JSON file could not be decoded or is invalid. "
                  "Error: {}").format(e),
            )
        method_name = "import_{}_{}".format(
            self.element_to_import, self.remotecontrol_type)
        if not hasattr(self, method_name):
            raise exceptions.UserError(
                _("The method '%s' is not implemented for the selected "
                  "element and remote control.") % method_name,
            )
        method = getattr(self, method_name)
        method(data, self.date)
