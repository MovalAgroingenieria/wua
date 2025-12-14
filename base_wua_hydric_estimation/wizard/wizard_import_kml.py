# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from lxml import etree

from odoo import models, fields, api, exceptions, _


class WizardKmlPlacemarkOption(models.TransientModel):
    _name = 'wizard.kml.placemark.option'
    _description = 'Placemark options detected in KML'

    wizard_id = fields.Many2one(
        string='Related Wizard',
        comodel_name='wizard.import.kml',
        ondelete='cascade',
    )

    name = fields.Char(
        string='Placemark Name',
    )


class WizardImportKml(models.TransientModel):
    _name = 'wizard.import.kml'
    _description = 'Wizard to import the geometry of a crop unit'

    KML_NAMESPACE = 'http://www.opengis.net/kml/2.2'

    cropunit_id = fields.Many2one(
        string='Crop Unit',
        comodel_name='wua.cropunit',
    )

    cropunit_description = fields.Char(
        string='Description of the crop unit',
    )

    kml_file = fields.Binary(
        string='KML File',
    )

    filename = fields.Char(
        string='File Name',
    )

    placemark_id = fields.Many2one(
        string='Polygon Identifier',
        comodel_name='wizard.kml.placemark.option',
    )

    @api.model
    def default_get(self, var_fields):
        cropunit_id = None
        cropunit_description = ''
        active_id = self.env.context['active_id']
        if active_id:
            cropunit = self.env['wua.cropunit'].browse(active_id)
            if cropunit:
                cropunit_id = cropunit.id
                cropunit_description = cropunit.name
        return {
            'cropunit_id': cropunit_id,
            'cropunit_description': cropunit_description,
        }

    @api.onchange('kml_file')
    def _onchange_file(self):
        self.placemark_id = False
        self.env['wizard.kml.placemark.option'].search([]).unlink()
        if self.kml_file:
            try:
                kml_data = base64.b64decode(self.kml_file)
                root = etree.fromstring(kml_data)
            except Exception:
                raise exceptions.UserError(_('The file is not a valid KML.'))
            ns = {'kml': self.KML_NAMESPACE}
            placemarks = root.findall('.//kml:Placemark', namespaces=ns)
            if not placemarks:
                raise exceptions.UserError(_('The KML file does not contain '
                                             'geometries.'))
            options = []
            for pm in placemarks:
                name = pm.findtext('kml:name', default=_('unnamed'),
                                   namespaces=ns)
                options.append((0, 0, {'name': name}))
            self.write({'placemark_id': False})
            for vals in (options or []):
                self.env['wizard.kml.placemark.option'].create({
                    'wizard_id': self.id,
                    'name': vals[2]['name'],
                })
            if options:
                self.placemark_id = \
                    self.env['wizard.kml.placemark.option'].search(
                        [('wizard_id', '=', self.id)], limit=1)

    def import_kml(self):
        if not self.cropunit_id:
            raise exceptions.UserError(
                _('There is no crop unit.'))
        parcel_id = self.cropunit_id.parcel_id
        if not parcel_id.mapped_to_polygon:
            raise exceptions.UserError(
                _('The parcel to which the crop unit belongs has no '
                  'geometry.'))
        import_ok = True
        # TODO (process...)
        if import_ok:
            # Provisional
            # self.cropunit_id.refresh_aerial_img()
            pass
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
