# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import io
import zipfile

from odoo import models, fields, api, exceptions, _


class WizardExportImagesZip(models.TransientModel):
    _name = 'wizard.export.images.zip'

    name = fields.Char(
        string='File Name',
        readonly=True,
    )
    data = fields.Binary(
        string='File',
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('choose', 'choose'),
            ('get', 'get'),
        ],
        default='choose',
    )
    export_before = fields.Boolean(
        string='Before images',
        default=True,
    )
    export_after = fields.Boolean(
        string='After images',
        default=True,
    )
    export_field = fields.Boolean(
        string='Field images',
        default=True,
    )

    @api.model
    def _sanitize_filename(self, name):
        """Replace characters that are not safe for filenames."""
        if not name:
            return 'unnamed'
        return name.replace('/', '-').replace('\\', '-').replace(
            ':', '-').replace('*', '-').replace('?', '-').replace(
            '"', '-').replace('<', '-').replace('>', '-').replace(
            '|', '-')

    @api.model
    def _get_request_folder_name(self, request):
        """Build a folder name for a maintenance request."""
        parts = []
        if request.sequence:
            parts.append(request.sequence)
        if request.equipment_id:
            parts.append(request.equipment_id.name or '')
        if not parts:
            parts.append(str(request.id))
        return self._sanitize_filename('_'.join(parts))

    @api.model
    def _add_images_to_zip(
            self, zip_file, folder_path, attachment_records,
            legacy_image=False, legacy_filename=False):
        """Add images from attachment records and/or a legacy binary
        field to the zip file.
        Returns the number of images added.
        """
        count = 0
        used_names = set()
        # Add images from One2many attachment records
        for att in attachment_records:
            if att.image:
                fname = att.filename or ('image_%d.jpg' % att.id)
                # Avoid duplicate names within the same folder
                if fname in used_names:
                    name_base, name_ext = (
                        fname.rsplit('.', 1) if '.' in fname
                        else (fname, 'jpg'))
                    fname = '%s_%d.%s' % (name_base, att.id, name_ext)
                used_names.add(fname)
                zip_file.writestr(
                    '%s/%s' % (folder_path, fname),
                    base64.b64decode(att.image),
                )
                count += 1
        # Add legacy single binary image if present and no O2M images
        if legacy_image and count == 0:
            fname = legacy_filename or 'image.jpg'
            zip_file.writestr(
                '%s/%s' % (folder_path, fname),
                base64.b64decode(legacy_image),
            )
            count += 1
        return count

    @api.multi
    def action_export_images_zip(self):
        """Export selected image types from maintenance requests
        into a ZIP file and present the download in the wizard.
        """
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise exceptions.UserError(
                _('No maintenance requests selected.'))
        requests = self.env['maintenance.request'].browse(
            active_ids)
        zip_buffer = io.BytesIO()
        total_images = 0

        with zipfile.ZipFile(
                zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
            for req in requests:
                folder = self._get_request_folder_name(req)
                before_label = _('before')
                after_label = _('after')
                field_label = _('field')
                # Before images
                if self.export_before:
                    total_images += self._add_images_to_zip(
                        zf,
                        '%s/%s' % (folder, before_label),
                        req.resolution_images_before,
                        legacy_image=(
                            req.resolution_image_before),
                        legacy_filename=(
                            req
                            .resolution_image_before_filename
                        ),
                    )
                # After images
                if self.export_after:
                    total_images += self._add_images_to_zip(
                        zf,
                        '%s/%s' % (folder, after_label),
                        req.resolution_images_after,
                        legacy_image=(
                            req.resolution_image_after),
                        legacy_filename=(
                            req
                            .resolution_image_after_filename
                        ),
                    )
                # Field images
                if self.export_field:
                    total_images += self._add_images_to_zip(
                        zf,
                        '%s/%s' % (folder, field_label),
                        req.field_images,
                        legacy_image=req.field_image,
                    )
        if total_images == 0:
            raise exceptions.UserError(
                _('No images found for the selected '
                  'maintenance requests.'))
        zip_data = base64.b64encode(zip_buffer.getvalue())
        filename = _('maintenance_images') + '.zip'
        self.write({
            'state': 'get',
            'data': zip_data,
            'name': filename,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.export.images.zip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
