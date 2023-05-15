# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardPreviewPublicationtext(models.TransientModel):
    _name = 'wizard.preview.publicationtext'
    _description = 'Dialog box to show the preview of the publication text'

    publication_text_preview = fields.Html(
        string='Preview of the header of the assembly convocation')

    @api.model
    def default_get(self, var_fields):
        publication_text_preview = ''
        assembly_id = self.env.context['active_id']
        show_final_paragraph = self.env.context.get(
            'show_final_paragraph', False)
        assembly = self.env['wua.assembly'].browse(assembly_id)
        if assembly_id:
            if show_final_paragraph:
                publication_text_preview = assembly.rendered_final_paragraph
            else:
                publication_text_preview = assembly.rendered_publication_text
        return {
            'publication_text_preview': publication_text_preview,
            }
