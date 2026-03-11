# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import io
import zipfile

from odoo import models, api, _


class WizardExportImagesZip(models.TransientModel):
    _name = 'wizard.export.images.zip'

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
        """Export all before, after and field images from the selected
        maintenance requests into a ZIP file organized by folders.
        Folder structure:
          <sequence>_<equipment>/
            before/
              image1.jpg
            after/
              image2.jpg
            field/
              image3.jpg
        """
        active_ids = self.env.context.get('active_ids', [])
        requests = self.env['maintenance.request'].browse(active_ids)
        if not requests:
            return
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        zip_buffer = io.BytesIO()
        total_images = 0

        with zipfile.ZipFile(
                zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:
            for request in requests:
                folder = self._get_request_folder_name(request)
                before_label = _('before')
                after_label = _('after')
                field_label = _('field')
                # Before images
                total_images += self._add_images_to_zip(
                    zip_file,
                    '%s/%s' % (folder, before_label),
                    request.resolution_images_before,
                    legacy_image=request.resolution_image_before,
                    legacy_filename=(
                        request.resolution_image_before_filename),
                )
                # After images
                total_images += self._add_images_to_zip(
                    zip_file,
                    '%s/%s' % (folder, after_label),
                    request.resolution_images_after,
                    legacy_image=request.resolution_image_after,
                    legacy_filename=(
                        request.resolution_image_after_filename),
                )
                # Field images
                total_images += self._add_images_to_zip(
                    zip_file,
                    '%s/%s' % (folder, field_label),
                    request.field_images,
                    legacy_image=request.field_image,
                )
        if total_images == 0:
            return
        result = base64.b64encode(zip_buffer.getvalue())
        filename = _('maintenance_images') + '.zip'
        attachment_obj = self.sudo().env['ir.attachment']
        # Clean previous temporary downloads
        attachment_obj.search([
            ('name', '=', 'maintenance_images_zip_download'),
            ('res_model', '=', 'maintenance.request'),
        ]).unlink()
        # Create new attachment
        attachment_id = attachment_obj.create({
            'name': 'maintenance_images_zip_download',
            'datas_fname': filename,
            'datas': result,
            'res_model': 'maintenance.request',
        })
        download_url = '/web/content/%s?download=true' % (
            str(attachment_id.id))
        return {
            'type': 'ir.actions.act_url',
            'url': '%s%s' % (str(base_url), str(download_url)),
            'target': 'new',
        }
