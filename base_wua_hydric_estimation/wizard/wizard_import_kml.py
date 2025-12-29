# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from lxml import etree

from odoo import models, fields, api, exceptions, _


class WizardKmlPlacemarkOption(models.TransientModel):
    _name = 'wizard.kml.placemark.option'
    _description = 'Placemark options detected in KML'

    session_key = fields.Char(
        string='Session Identifier',
    )

    name = fields.Char(
        string='Placemark Name',
    )


class WizardImportKml(models.TransientModel):
    _name = 'wizard.import.kml'
    _description = 'Wizard to import the geometry of a crop unit'

    KML_NAMESPACE = 'http://www.opengis.net/kml/2.2'

    def _get_placemark_id_domain(self):
        resp = None
        session_key = self.env.context.get('session_key', False)
        if session_key:
            return [('session_key', '=', session_key)]
        return resp

    session_key = fields.Char(
        string='Session Key',
    )

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
        domain=_get_placemark_id_domain,
        ondelete='set null',
    )

    @api.model
    def default_get(self, var_fields):
        cropunit_id = None
        cropunit_description = ''
        session_key = self.env.context.get('session_key', False)
        active_id = self.env.context['active_id']
        if active_id:
            cropunit = self.env['wua.cropunit'].browse(active_id)
            if cropunit:
                cropunit_id = cropunit.id
                cropunit_description = cropunit.name
                # Remove the previous options assigned to this user and this
                # cultivation unit.
                if not session_key:
                    session_key = str(self.env.user.id) + '-' + cropunit.name
                # DO NOT uncomment! -> Foreign key error -> Solution: do this
                # from the caller (problem: "default_gets" is called twice, the
                # last time after clicking the "Apply" button).
                # prev_options = self.env['wizard.kml.placemark.option'].search(
                #     [('session_key', '=', session_key)])
                # if prev_options:
                #     prev_options.unlink()
        return {
            'cropunit_id': cropunit_id,
            'cropunit_description': cropunit_description,
            'session_key': session_key,
        }

    @api.onchange('kml_file')
    def _onchange_kml_file(self):
        if self.kml_file:
            try:
                kml_data = base64.b64decode(self.kml_file)
                root = etree.fromstring(kml_data)
            except Exception:
                self._drop_options(self.session_key)
                raise exceptions.UserError(_('The file is not a valid KML.'))
            ns = {'kml': self.KML_NAMESPACE}
            placemarks = root.findall('.//kml:Placemark', namespaces=ns)
            if not placemarks:
                self._drop_options(self.session_key)
                raise exceptions.UserError(_('The KML file does not contain '
                                             'geometries.'))
            placemark_names = []
            for placemark in placemarks:
                name = placemark.findtext('kml:name', default=_('unnamed'),
                                          namespaces=ns)
                placemark_names.append(name)
            model_placemark_option = self.env['wizard.kml.placemark.option']
            prev_options = model_placemark_option.search(
                [('session_key', '=', self.session_key)])
            self._drop_options(self.session_key)
            if placemark_names:
                for name in placemark_names:
                    new_option = model_placemark_option.create({
                        'session_key': self.session_key,
                        'name': name,
                    })
                first_option = model_placemark_option.search(
                    [('session_key', '=', self.session_key)], limit=1)
                if first_option:
                    self.placemark_id = first_option.id

    @api.model
    def _drop_options(self, session_key):
        try:
            self.env.cr.savepoint()
            self.env.cr.execute(
                'DELETE FROM wizard_kml_placemark_option '
                'WHERE session_key = %s', (session_key,))
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()

    def import_kml(self):
        if not self.cropunit_id:
            raise exceptions.UserError(
                _('There is no crop unit.'))
        parcel = self.cropunit_id.parcel_id
        if not parcel.mapped_to_polygon:
            raise exceptions.UserError(
                _('The parcel to which the crop unit belongs has no '
                  'geometry.'))
        if (not self.kml_file) or (not self.placemark_id):
            raise exceptions.UserError(
                _('Polygon not found.'))
        model_cropunit = self.env['wua.cropunit']
        gis_table = model_cropunit.__class__._name.replace(
            '.', '_').replace('wua_', 'wua_gis_')
        import_ok, message_error = model_cropunit.create_polygon(
            self.placemark_id.name, self.kml_file,
            self.cropunit_id.name, gis_table, parcel.geom_ewkt)
        if import_ok:
            self.cropunit_id.calculate()
            self.cropunit_id.refresh_aerial_img()
        else:
            raise exceptions.UserError(message_error)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
