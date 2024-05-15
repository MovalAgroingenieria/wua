# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
import datetime
import pytz
from lxml import etree
from odoo import models, fields, api, _, exceptions


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    is_primary = fields.Boolean(
        string='Is primary',
        default=False,
    )

    partner_type = fields.Selection([
        ('01_WUA', 'Water User Association'),
        ('02_IND', 'Industry'),
        ('03_WSP', 'Water Supply'),
        ('04_HEL', 'Hydroelectric Producer'),
    ], string='Partner Type',
        related='partner_id.partner_type',
        store=True,
        radonly=True,
        index=True,
    )

    wuabase_id = fields.Many2one(
        string='Primary Entity',
        comodel_name='wua.wuabase',
        index=True,
    )

    octroi_id = fields.Many2one(
        string='Octroi',
        related='intake_id.octroi_id',
        comodel_name='wua.octroi',
        store=True,
        index=True,
        readonly=True,
    )

    waterchannel_id = fields.Many2one(
        string='Waterchannel',
        related='intake_id.waterchannel_id',
        comodel_name='wua.waterchannel',
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains('is_primary', 'parcel_class_ids')
    def check_primary_parcel_class(self):
        for record in self:
            if record.is_primary and len(record.parcel_class_ids) != 0:
                raise exceptions.ValidationError(
                    _('A primary parcel cannot have a class associated.'))
            elif not record.is_primary and len(record.parcel_class_ids) < 1:
                raise exceptions.ValidationError(
                    _('A che parcel must have at least one class associated.'))

    @api.constrains('is_primary', 'partnerlink_ids')
    def check_primary_partnerlinks(self):
        for record in self:
            if (len(record.partnerlink_ids) > 0):
                # Primary cannot have more than one partnerlink and this¡
                # partner must be primary
                if record.is_primary and (
                    len(record.partnerlink_ids) > 1 or
                    len(record.partnerlink_ids.filtered(
                        lambda x: not x.partner_id.is_primary)) > 0):
                    raise exceptions.ValidationError(
                        _('A primary parcel cannot have a non primary '
                          'partner.'))
                elif not record.is_primary and len(
                    record.partnerlink_ids.filtered(
                        lambda x: x.partner_id.is_primary)) > 0:
                    raise exceptions.ValidationError(
                        _('A CHE parcel cannot have a non CHE '
                          'partner.'))

    def _compute_partner_id(self):
        super(WuaParcel, self)._compute_partner_id()
        for record in self:
            if not record.wuabase_id and record.partner_id.wuabase_id:
                parcel_id = record.id
                wuabase_id = record.partner_id.wuabase_id.id
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                    UPDATE wua_parcel SET wuabase_id=%s
                    WHERE id=%s""", (wuabase_id, parcel_id))
                    self.env.cr.execute("""
                    UPDATE wua_parcel_class SET wuabase_id=%s
                    WHERE parcel_id=%s""", (wuabase_id, parcel_id))
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()

    # Inherit method to ensure that parcels not primary have at least
    # one parcel class on creation
    def should_create_parcel_class_on_creation(self, parcel_vals):
        return super(WuaParcel, self).should_create_parcel_class_on_creation(
            parcel_vals) and ('is_primary' not in parcel_vals or
                              not parcel_vals['is_primary'])

    def populate_area_official_of_parcel_class(
            self, parcel_class_ids, area_official):
        # if the record is the first class of the parcel
        # and the area is 0, then populate the area.
        if len(parcel_class_ids) == 1 and parcel_class_ids[0][0] == 0:
            vals = parcel_class_ids[0][2]
            if vals['area_official'] == 0:
                vals.update({'area_official': area_official})

    # If the area_official parameter is -1, then find parcel
    # from parcel_id and get her area. If the parcel_class_ids parameter
    # is None, then find all parcel_classes from parcel_id and sum their area.
    # Primary parcels don't have parcel classes
    def is_parcel_classes_area_correct(
            self, parcel_id, area_official, parcel_class_ids, parcel_vals):
        parcels = self.env['wua.parcel']
        parcel = parcels.browse(parcel_id)
        if (('is_primary' in parcel_vals and parcel_vals['is_primary']) or
                (parcel.is_primary and 'is_primary' not in parcel_vals)):
            return True
        else:
            total_area = 0
            if area_official == -1:
                parcels = self.env['wua.parcel']
                parcel = parcels.browse(parcel_id)
                if parcel:
                    area_official = parcel.area_official
            unchanged_ids = []
            condition = []
            if parcel_class_ids is not None:
                for parcel_class in parcel_class_ids:
                    parcel_class_oper = parcel_class[0]
                    parcel_class_id = parcel_class[1]
                    parcel_class_vals = parcel_class[2]
                    # unmodified area
                    if parcel_class_oper == 4 or (
                        parcel_class_oper == 1 and 'area_official' not in
                            parcel_class_vals):
                        unchanged_ids.append(parcel_class_id)
                    # append parcel_class or update parcel_class with modified
                    # area
                    if parcel_class_oper == 0 or (
                        parcel_class_oper == 1 and 'area_official' in
                            parcel_class_vals):
                        total_area = total_area + \
                            parcel_class_vals['area_official']
                if len(unchanged_ids) > 0:
                    condition = [('id', 'in', unchanged_ids)]
                    parcel_classs = self.env['wua.parcel.class']
                    filtered_parcel_classes = parcel_classs.search(condition)
                    for parcel_class in filtered_parcel_classes:
                        total_area = total_area + parcel_class.area_official
            else:
                condition = [('parcel_id', '=', parcel_id)]
                parcel_classes = self.env['wua.parcel.class']
                filtered_parcel_classes = parcel_classes.search(condition)
                for parcel_class in filtered_parcel_classes:
                    total_area = total_area + parcel_class.area_official
            # return area_official == total_area
            return self.is_close(area_official, total_area)

    def is_subparcels_area_correct(self, parcel_id,
                                   area_official, subparcel_ids):
        if area_official >= 0:
            try:
                # In CAyC, only one subparcel per parcel.
                self.env.cr.savepoint()
                self.env.cr.execute("""
                UPDATE wua_parcel_subparcel SET area_official=%s
                WHERE parcel_id=%s""", (area_official, parcel_id))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
        return True

    def do_process_slave_data_for_write(self, vals):
        super(WuaParcel, self).do_process_slave_data_for_write(vals)
        area_official = -1
        parcel_class_ids = None
        if 'area_official' in vals:
            area_official = vals['area_official']
        if 'parcel_class_ids' in vals:
            parcel_class_ids = vals['parcel_class_ids']
        correct_subparcels_area = self.is_parcel_classes_area_correct(
            self.id, area_official, parcel_class_ids, vals)
        if not correct_subparcels_area:
            raise exceptions.UserError(_('The sum of parcel class areas '
                                         'must be the parcel official '
                                         'area.'))

    @api.model
    def create(self, vals):
        if 'parcel_class_ids' in vals:
            self.populate_area_official_of_parcel_class(
                vals['parcel_class_ids'], vals['area_official'])
        if self.should_create_parcel_class_on_creation(vals):
            self.populate_parcel_class_for_creation(vals)
        new_parcel = super(WuaParcel, self).create(vals)
        correct_parcel_classes_area = self.is_parcel_classes_area_correct(
            new_parcel.id, vals['area_official'],
            vals['parcel_class_ids'], vals)
        if not correct_parcel_classes_area:
            raise exceptions.UserError(_('The sum of classes areas must '
                                         'be the parcel official area.'))
        return new_parcel

    # Replaced
    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        # Should be a parameter?
        wuabase_param = 'wuabaseid'
        for record in self:
            url_for_record = url
            if url_for_record:
                param_for_url = parcel_param
                if (record.is_primary):
                    param_for_url = wuabase_param
                if param_for_url:
                    sep_char = u'?'
                    if url_for_record.find('?') != -1:
                        sep_char = u'&'
                    url_for_record = url_for_record + sep_char + \
                        param_for_url + u'=' + record.name
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                credentials = username + "-" + password
                credentials = credentials.ljust(32)
                current_datetime = pytz.utc.localize(datetime.datetime.now())
                current_datetime = current_datetime.astimezone(
                    pytz.timezone('Europe/Madrid'))
                current_datetime = str(current_datetime)[:16].replace(' ', 'T')
                minimum = int(current_datetime[14:])
                if minimum < 30:
                    minimum = '00'
                else:
                    minimum = '30'
                iv = current_datetime[:14] + minimum
                aes_encryptor = AES.new('z%C*F-JaNdRgUkXp', AES.MODE_CBC, iv)
                cipher_text = aes_encryptor.encrypt(credentials)
                cipher_text = cipher_text.encode('base64')
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                url_for_record = url_for_record + sep_char + \
                    "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    # Added set gis fields for parcels primary
    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        gis_parcels_primary_ok = True
        area_measurement_equivalence = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = \
                self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_equivalence')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                UPDATE public.wua_parcel wp1
                SET with_gis_parcel = TRUE, area_gis =
                (postgis.ST_Area(wgw1.geom) * 0.0001) / %s
                FROM public.wua_gis_wuabase wgw1 WHERE wp1.name = wgw1.name;
            """, [area_measurement_equivalence])
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            gis_parcels_ok = False
        return gis_parcels_ok and gis_parcels_primary_ok

    # Aerial image changes for primary parcels
    def _get_aerial_image_layers(self, parcel):
        layers_for_wms = self._aerial_img_layers
        if (parcel.is_primary):
            layers_for_wms = [
                'pnoa', 'wuabase', 'wuabase_perimeter', 'n_arrow']
        return layers_for_wms

    def _get_wfs_response(self, wfs, parcel):
        typename = 'fes:parcel'
        if (parcel.is_primary):
            typename = 'fes:wuabase'
        filterxml = '<Filter><PropertyIsEqualTo><ValueReference>name' +\
            '</ValueReference><Literal>' + parcel.name + '</Literal>' +\
            '</PropertyIsEqualTo></Filter>'
        response = wfs.getfeature(typename=typename, filter=filterxml)
        return response

    def get_sld_body(self):
        body = ''
        if (self.is_primary):
            body = body + '<?xml version="1.0" encoding="UTF-8"?>' +\
                '<StyledLayerDescriptor version="1.0.0" ' + \
                'xmlns="http://www.opengis.net/sld" xmlns:ogc="' +\
                'http://www.opengis.net/ogc" xmlns:xlink="' +\
                'http://www.w3.org/1999/xlink" xmlns:xsi="' +\
                'http://www.w3.org/2001/XMLSchema-instance"' +\
                'xsi:schemaLocation="http://www.opengis.net/sld ' +\
                'http://schemas.opengis.net/sld/1.0.0/StyledLaye' +\
                'rDescriptor.xsd">' +\
                '<NamedLayer><Name>wuabase</Name>' +\
                '<UserStyle><Title>xxx</Title><FeatureTypeStyle>' +\
                '<Rule><Filter><PropertyIsLike ' +\
                'wildCard="*" singleChar="." escape="!"><Property' +\
                'Name>name</PropertyName><Literal>' + self.name +\
                '</Literal></PropertyIsLike></Filter>' +\
                '<PolygonSymbolizer>' +\
                '<Stroke>' +\
                '<CssParameter name="stroke">#000000</CssParameter>' +\
                '<CssParameter name="stroke-width">14</CssParameter>' +\
                '<CssParameter name="stroke-linecap">round</CssParameter>' +\
                '</Stroke>' +\
                '</PolygonSymbolizer>' +\
                '</Rule></FeatureTypeStyle>' +\
                '</UserStyle></NamedLayer>' +\
                '<NamedLayer><Name>wuabase_perimeter</Name>' +\
                '<UserStyle><Title>xxx2</Title><FeatureTypeStyle>' +\
                '<Rule><Filter><PropertyIsLike ' +\
                'wildCard="*" singleChar="." escape="!"><Property' +\
                'Name>name</PropertyName><Literal>' + self.name +\
                '</Literal></PropertyIsLike></Filter>' +\
                '<PolygonSymbolizer>' +\
                '<Stroke>' +\
                '<CssParameter name="stroke">#ffffff</CssParameter>' +\
                '<CssParameter name="stroke-width">5</CssParameter>' +\
                '<CssParameter name="stroke-linecap">round</CssParameter>' +\
                '</Stroke>' +\
                '</PolygonSymbolizer>' +\
                '</Rule></FeatureTypeStyle>' +\
                '</UserStyle></NamedLayer>' +\
                '</StyledLayerDescriptor>'
        else:
            body = body + super(WuaParcel, self).get_sld_body()
        return body

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        result = super(WuaParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            if (self.env.context.get('is_primary_parcel', False)):
                hide_fields = [
                    'wuabase_id',
                    'intake_id',
                    'class_sharer',
                ]
            else:
                hide_fields = [
                    'mapped_to_current_quotaperiod',
                    'cadastral_polygon',
                    'cadastral_parcel',
                    'cadastral_reference',
                ]
            for field in hide_fields:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            result['arch'] = etree.tostring(doc)
        return result


class WuaParcelClass(models.Model):
    _inherit = 'wua.parcel.class'

    wuabase_id = fields.Many2one(
        string='Primary Entity',
        comodel_name='wua.wuabase',
        related='parcel_id.wuabase_id',
        store=True,
        index=True,
        readonly=True,
    )

    intake_id = fields.Many2one(
        string='Intake',
        related='parcel_id.intake_id',
        comodel_name='wua.intake',
        store=True,
        index=True,
        readonly=True,
    )

    octroi_id = fields.Many2one(
        string='Octroi',
        related='parcel_id.octroi_id',
        comodel_name='wua.octroi',
        store=True,
        index=True,
        readonly=True,
    )

    waterchannel_id = fields.Many2one(
        string='Waterchannel',
        related='parcel_id.waterchannel_id',
        comodel_name='wua.waterchannel',
        store=True,
        index=True,
        readonly=True,
    )
