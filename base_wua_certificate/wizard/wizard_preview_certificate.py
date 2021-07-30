# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardPreviewCertificate(models.TransientModel):
    _name = 'wizard.preview.certificate'
    _description = 'Dialog box to show the preview of certificate'

    main_page_preview = fields.Html(
        string='Preview of certificate')

    @api.model
    def default_get(self, var_fields):
        main_page_preview = ''
        certificate_id = self.env.context['active_id']
        certificate = self.env['wua.certificate'].browse(certificate_id)
        if certificate_id:
            main_page_preview = certificate.rendered_main_page
            if main_page_preview:
                main_page_preview = certificate.html_certificate_title + \
                    '<br><br>' + main_page_preview
        return {
            'main_page_preview': main_page_preview,
            }
