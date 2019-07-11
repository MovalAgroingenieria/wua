# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from pyproj import Proj, transform
from odoo import models, fields, api,  exceptions, _
import logging
from shapely import wkb


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    SIZE_IRRIGATIONPOINT_SUFFIX = 2
    SIZE_TRACK = 510

    irrigationpoint_ids = fields.One2many(
        string='Irrigation Points',
        comodel_name='wua.parcel.irrigationpoint',
        inverse_name='parcel_id')

    irrigationpointwc_ids = fields.One2many(
        string='Irrigation Points (WC)',
        comodel_name='wua.parcel.irrigationpointwc',
        inverse_name='parcel_id')

    number_of_irrigationpoints = fields.Integer(
        string='Irrigation Points',
        store=True,
        compute='_compute_number_of_irrigationpoints')

    hydraulic_infrastructure_type = fields.Selection([
        (0, 'No infrastructure'),
        (1, 'Pressurized Irrigation'),
        (2, 'Gravity Irrigation'),
        (3, 'Pressurized and Gravity fed Irrigation'),
        ], string='Infrastructure',
        store=True,
        compute='_compute_hydraulic_infrastructure_type')

    pressurized_irrigation_right = fields.Boolean(
        string="Water Right (pres)",
        default=True)

    gravityfed_irrigation_right = fields.Boolean(
        string="Water Right (grav)",
        default=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        store=True,
        compute='_compute_hydraulicsector_id',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute='_compute_irrigationditch_id',
        ondelete='restrict')

    with_watering_shift = fields.Boolean(
        string="With Watering Shift",
        default=True)

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker",
        default=False)

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        index=True,
        ondelete='restrict')

    track_irrigationpointwc_ids = fields.Char(
        string='Water Connections',
        size=SIZE_TRACK,
        store=True,
        compute='_compute_track_irrigationpointwc_ids',
        track_visibility='onchange')

    track_subparcel_irrigationgate_ids = fields.Char(
        string='Subparcel Irrigation Gates',
        size=SIZE_TRACK,
        store=True,
        compute='_compute_track_subparcel_irrigationgate_ids',
        track_visibility='onchange')

    @api.depends('irrigationpoint_ids')
    def _compute_number_of_irrigationpoints(self):
        if len(self) == 1:
            self.number_of_irrigationpoints = len(self.irrigationpoint_ids)
        else:
            for parcel in self:
                parcel.number_of_irrigationgates = \
                    len(parcel.irrigationpoint_ids)

    @api.depends('irrigationpoint_ids')
    def _compute_hydraulic_infrastructure_type(self):
        for record in self:
            hydraulic_infrastructure_type = 0
            for irrigation_point in record.irrigationpoint_ids:
                if hydraulic_infrastructure_type == 0:
                    if irrigation_point.type == 'WC':
                        hydraulic_infrastructure_type = 1
                    if irrigation_point.type == 'IG':
                        hydraulic_infrastructure_type = 2
                if (hydraulic_infrastructure_type == 1 and
                   irrigation_point.type == 'IG'):
                    hydraulic_infrastructure_type = 3
                if (hydraulic_infrastructure_type == 2 and
                   irrigation_point.type == 'WC'):
                    hydraulic_infrastructure_type = 3
                if hydraulic_infrastructure_type == 3:
                    break
            record.hydraulic_infrastructure_type = \
                hydraulic_infrastructure_type

    @api.depends('irrigationpoint_ids')
    def _compute_hydraulicsector_id(self):
        for record in self:
            irrigation_points = record.irrigationpoint_ids
            hydraulicsector_id = None
            if len(irrigation_points) > 0:
                for irrigation_point in irrigation_points:
                    if irrigation_point.type == 'WC':
                        hydraulicsector_id = irrigation_point.\
                            waterconnection_id.hydraulicsector_id
                        break
            record.hydraulicsector_id = hydraulicsector_id

    @api.depends('irrigationpoint_ids')
    def _compute_irrigationditch_id(self):
        for record in self:
            irrigation_points = record.irrigationpoint_ids
            irrigationditch_id = None
            if len(irrigation_points) > 0:
                for irrigation_point in irrigation_points:
                    if irrigation_point.type == 'IG':
                        irrigationditch_id = irrigation_point.\
                            irrigationgate_id.irrigationditch_id
                        break
            record.irrigationditch_id = irrigationditch_id

    @api.depends('irrigationpointwc_ids')
    def _compute_track_irrigationpointwc_ids(self):
        for record in self:
            track_irrigationpointwc_ids = ''
            for irrigationpointwc in record.irrigationpointwc_ids:
                track_irrigationpointwc_ids = track_irrigationpointwc_ids + \
                    irrigationpointwc.waterconnection_id.name + ', '
            if track_irrigationpointwc_ids != '':
                track_irrigationpointwc_ids = track_irrigationpointwc_ids[:-2]
            record.track_irrigationpointwc_ids = track_irrigationpointwc_ids

    @api.depends('subparcel_ids.irrigationgate_id')
    def _compute_track_subparcel_irrigationgate_ids(self):
        for record in self:
            track_subparcel_irrigationgate_ids = ''
            for subparcel in record.subparcel_ids:
                subparcel_pos = str(subparcel.pos)
                irrigationgate_name = ''
                if subparcel.irrigationgate_id:
                    irrigationgate_name = subparcel.irrigationgate_id.name
                track_subparcel_irrigationgate_ids = \
                    track_subparcel_irrigationgate_ids + \
                    subparcel_pos + ': ' + irrigationgate_name + ', '
            if track_subparcel_irrigationgate_ids != '':
                track_subparcel_irrigationgate_ids = \
                    track_subparcel_irrigationgate_ids[:-2]
            record.track_subparcel_irrigationgate_ids = \
                track_subparcel_irrigationgate_ids

    @api.model
    def create(self, vals):
        new_parcel = super(WuaParcel, self).create(vals)
        filtered_subparcels = self.env['wua.parcel.subparcel'].search(
            [('parcel_id', '=', new_parcel.id)])
        if len(filtered_subparcels) > 0:
            irrigation_points = self.env['wua.parcel.irrigationpoint']
            for subparcel in filtered_subparcels:
                if subparcel.irrigationgate_id:
                    irrigation_points.create({
                        'parcel_id': new_parcel.id,
                        'type': 'IG',
                        'irrigationgate_id': subparcel.irrigationgate_id.id,
                        })
        filtered_irrigationpointswc = \
            self.env['wua.parcel.irrigationpointwc'].search(
                [('parcel_id', '=', new_parcel.id)])
        if len(filtered_irrigationpointswc) > 0:
            irrigation_points = self.env['wua.parcel.irrigationpoint']
            for irrigationpointwc in filtered_irrigationpointswc:
                irrigation_points.create({
                    'parcel_id': new_parcel.id,
                    'type': 'WC',
                    'waterconnection_id': (irrigationpointwc.
                                           waterconnection_id.id),
                    })
        return new_parcel

    @api.multi
    def write(self, vals):
        irrigationgates_to_add = []
        irrigationgates_to_del = []
        waterconnections_to_add = []
        waterconnections_to_del = []
        # Before "write": get id from irrigation gates to remove in
        # irrigation points table.
        if 'subparcel_ids' in vals:
            irrigationgates_to_del = \
                self.populate_irrigationgates_to_del(vals)
        if 'irrigationpointwc_ids' in vals:
            waterconnections_to_del = \
                self.populate_waterconnections_to_del(vals)
        # Call inherited write operation.
        super(WuaParcel, self).write(vals)
        # After "write": get id from irrigation gates to add in
        # irrigation points table.
        if 'subparcel_ids' in vals:
            irrigationgates_to_add =\
                self.populate_irrigationgates_to_add(vals)
        if 'irrigationpointwc_ids' in vals:
            waterconnections_to_add =\
                self.populate_waterconnections_to_add(vals)
        irrigation_points = self.env['wua.parcel.irrigationpoint']
        if len(irrigationgates_to_del) > 0:
            irrigation_points_to_del = irrigation_points.search(
                [('parcel_id', '=', self.id),
                 ('irrigationgate_id', 'in', irrigationgates_to_del)])
            irrigation_points_to_del.unlink()
        if len(irrigationgates_to_add) > 0:
            for irrigationgate_id in irrigationgates_to_add:
                irrigation_points.create({
                    'parcel_id': self.id,
                    'type': 'IG',
                    'irrigationgate_id': irrigationgate_id,
                    })
        if len(waterconnections_to_del) > 0:
            irrigation_points_to_del = irrigation_points.search(
                [('parcel_id', '=', self.id),
                 ('waterconnection_id', 'in', waterconnections_to_del)])
            irrigation_points_to_del.unlink()
        if len(waterconnections_to_add) > 0:
            for waterconnection_id in waterconnections_to_add:
                irrigation_points.create({
                    'parcel_id': self.id,
                    'type': 'WC',
                    'waterconnection_id': waterconnection_id,
                    })
        return True

    def populate_irrigationgates_to_del(self, vals):
        irrigationgates_to_del = []
        for subparcel in vals['subparcel_ids']:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if (subparcel_oper == 2 or (subparcel_oper == 1 and
               'irrigationgate_id' in subparcel_vals)):
                modified_subparcel = self.env['wua.parcel.subparcel'].\
                    browse(subparcel_id)
                if modified_subparcel:
                    if modified_subparcel.irrigationgate_id.id:
                        irrigationgates_to_del.\
                            append(modified_subparcel.irrigationgate_id.id)
        return irrigationgates_to_del

    def populate_waterconnections_to_del(self, vals):
        waterconnections_to_del = []
        for irrigationpointwc in vals['irrigationpointwc_ids']:
            irrigationpointwc_oper = irrigationpointwc[0]
            irrigationpointwc_id = irrigationpointwc[1]
            irrigationpointwc_vals = irrigationpointwc[2]
            if (irrigationpointwc_oper == 2 or
                (irrigationpointwc_oper == 1 and
                 'waterconnection_id' in irrigationpointwc_vals)):
                modified_irrigationpointwc = \
                    self.env['wua.parcel.irrigationpointwc'].\
                    browse(irrigationpointwc_id)
                if modified_irrigationpointwc:
                    if modified_irrigationpointwc.waterconnection_id.id:
                        waterconnections_to_del.append(
                            modified_irrigationpointwc.
                            waterconnection_id.id)
        return waterconnections_to_del

    @api.multi
    def action_update_gis_link(self):
        if self.check_gis():
            self.set_gis_fields()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Parcels',
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'context': self.env.context,
                }

    def check_gis(self):
        resp = False
        self.env.cr.execute("""
               SELECT EXISTS(SELECT * FROM information_schema.tables
               WHERE table_name='wua_gis_parcel')
               """)
        if self.env.cr.fetchone()[0]:
            resp = True
            self.env.cr.execute("""
                SELECT EXISTS(SELECT * FROM information_schema.tables
                WHERE table_name='wua_gis_irrigationshed')
                """)
        if not self.env.cr.fetchone()[0]:
            resp = False
        return resp

    def set_gis_fields(self):
        gis_parcels_ok = True
        try:
            self.env.cr.execute("""
            SELECT name, geom FROM public.wua_gis_parcel
            """)
        except:
            gis_parcels_ok = False
        if gis_parcels_ok:
            gis_parcels = self.env.cr.fetchall()
            area_measurement_equivalence = 1
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_equivalence = \
                    self.env['ir.values'].get_default(
                        'wua.configuration', 'area_measurement_equivalence')
            if gis_parcels:
                parcels = self.env['wua.parcel'].search([])
                number_of_gis_parcels = len(gis_parcels)
                number_of_parcels = len(parcels)
                self.env.cr.execute("""
                    UPDATE public.wua_parcel
                    SET area_gis = 0, with_gis_parcel = FALSE
                    """)
                for gis_parcel in gis_parcels:
                    name = gis_parcel[0]
                    geom = gis_parcel[1]
                    decoded_geom = wkb.loads(geom, True)
                    area_gis_m2 = decoded_geom.area
                    area_gis = (
                                area_gis_m2 * 0.0001 /
                                area_measurement_equivalence)
                    filtered_parcels = \
                        parcels.filtered(lambda x: x.name == name)
                    if len(filtered_parcels) == 1:
                        parcel = filtered_parcels[0]
                        parcel.area_gis = area_gis
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info('Matching GIS info...')
                    _logger.info(
                                'Number of Odoo-Parcels: ' +
                                str(number_of_parcels))
                    _logger.info(
                                'Number of GIS-Parcels : ' +
                                str(number_of_gis_parcels))
        gis_irrigationsheds_ok = True
        try:
            self.env.cr.execute("""
            SELECT name, geom FROM public.wua_gis_irrigationshed
            """)
        except:
            gis_irrigationsheds_ok = False
        if gis_irrigationsheds_ok:
            gis_irrigationsheds = self.env.cr.fetchall()
            if gis_irrigationsheds:
                irrigationsheds = self.env['wua.irrigationshed'].search([])
                number_of_gis_irrigationsheds = len(gis_irrigationsheds)
                number_of_irrigationsheds = len(irrigationsheds)
                self.env.cr.execute("""
                    UPDATE public.wua_irrigationshed
                    SET with_gis_irrigationshed = FALSE
                    """)
                for gis_irrigationshed in gis_irrigationsheds:
                    name = gis_irrigationshed[0]
                    geom = gis_irrigationshed[1]
                    decoded_geom = wkb.loads(geom, True)
                    point_gis = decoded_geom
                    filtered_irrigationsheds = \
                        irrigationsheds.filtered(lambda x: x.name == name)
                    if len(filtered_irrigationsheds) == 1:
                        irrigationshed = filtered_irrigationsheds[0]
                        irrigationshed.with_gis_irrigationshed = True
                        print point_gis.y
                        print point_gis.x
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info('Matching GIS info...')
                        _logger.info(
                                    'Number of Odoo-Irrigationsheds: ' +
                                    str(number_of_irrigationsheds))
                        _logger.info(
                                    'Number of GIS-Irrigationsheds : ' +
                                    str(number_of_gis_irrigationsheds))
        return gis_irrigationsheds_ok and gis_parcels_ok

    def populate_irrigationgates_to_add(self, vals):
        irrigationgates_to_add = []
        for subparcel in vals['subparcel_ids']:
            subparcel_oper = subparcel[0]
            subparcel_vals = subparcel[2]
            if ((subparcel_oper == 0 and
                 'irrigationgate_id' in subparcel_vals) or
                (subparcel_oper == 1 and
                 'irrigationgate_id' in subparcel_vals)):
                if subparcel_vals['irrigationgate_id']:
                    irrigationgates_to_add.\
                        append(subparcel_vals['irrigationgate_id'])
        return irrigationgates_to_add

    def populate_waterconnections_to_add(self, vals):
        waterconnections_to_add = []
        for irrigationpointwc in vals['irrigationpointwc_ids']:
            irrigationpointwc_oper = irrigationpointwc[0]
            irrigationpointwc_vals = irrigationpointwc[2]
            if (irrigationpointwc_oper == 0 or
                (irrigationpointwc_oper == 1 and
                 'waterconnection_id' in irrigationpointwc_vals)):
                if irrigationpointwc_vals['waterconnection_id']:
                    waterconnections_to_add.append(
                        irrigationpointwc_vals['waterconnection_id'])
        return waterconnections_to_add

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcel, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_form(doc)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_search(doc)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_tree(doc)
        return res

    def fields_view_get_form(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            self.fields_view_get_form_irrigation_model_type_0(doc)
        if irrigation_model_type == 1:
            self.fields_view_get_form_irrigation_model_type_1(doc)
        if irrigation_model_type == 1 or irrigation_model_type == 2:
            for node in doc.xpath(
                    "//page[@name='subparcels']"):
                node.set('string', _('Subparc. / Irrig. Gates'))
        disable_edit_parcel_in_context = \
            self.env.context.get('disable_edit_parcel')
        if disable_edit_parcel_in_context == '1':
            for node in doc.xpath(
                    "//form[@duplicate='false']"):
                node.set('create', 'false')
                node.set('edit', 'false')
                node.set('delete', 'false')
        return etree.tostring(doc)

    def fields_view_get_form_irrigation_model_type_0(self, doc):
        for node in doc.xpath(
                "//field[@name='irrigationditch_id']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='gravityfed_irrigation_right']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='with_watering_shift']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='with_irrigation_worker']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='employee_id']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')

    def fields_view_get_form_irrigation_model_type_1(self, doc):
        for node in doc.xpath(
                "//field[@name='hydraulicsector_id']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='pressurized_irrigation_right']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//page[@name='irrigation_supplies']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')

    def fields_view_get_search(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            self.fields_view_get_search_irrigation_model_type_0(doc)
        if irrigation_model_type == 1:
            self.fields_view_get_search_irrigation_model_type_1(doc)
        return etree.tostring(doc)

    def fields_view_get_search_irrigation_model_type_0(self, doc):
        for node in doc.xpath(
                "//field[@name='irrigationditch_id']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulic_infrastructure_type_2']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulic_infrastructure_type_3']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='gravityfedirrigation']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='irrigationditch']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='withirrigationworker']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='irrigationworker']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')

    def fields_view_get_search_irrigation_model_type_1(self, doc):
        for node in doc.xpath(
                "//field[@name='hydraulicsector_id']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulic_infrastructure_type_1']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulic_infrastructure_type_3']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='pressurizedirrigation']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulicsector']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, "invisible": true}')

    def fields_view_get_tree(self, doc):
        disable_edit_parcel_in_context = \
            self.env.context.get('disable_edit_parcel')
        if disable_edit_parcel_in_context == '1':
            for node in doc.xpath(
                    "//tree[@class='o_base_wua_parcel_view_tree']"):
                node.set('create', 'false')
                node.set('edit', 'false')
                node.set('delete', 'false')
        return etree.tostring(doc)

    def populate_irrigationpointwccode_pos(self, parcel_name, vals):
        # parcel_name == False -> create a new parcel, and update all
        #                irrigation points (get parcel_name from vals).
        # parcel_name != False and parcel_name not in vals -> write existing
        #                parcel, and update only new irrigation points.
        # parcel_name != False and parcel_name in vals -> it is not possible,
        #                (readonly="true" in edit mode).
        if vals and 'irrigationpointwc_ids' in vals:
            if not parcel_name:
                parcel_name = vals['name']
            last_pos = 0
            max_irrigationpointwc_id = 0
            for irrigationpointwc in vals['irrigationpointwc_ids']:
                irrigationpointwc_oper = irrigationpointwc[0]
                irrigationpointwc_id = irrigationpointwc[1]
                if irrigationpointwc_oper == 1 or irrigationpointwc_oper == 4:
                    if irrigationpointwc_id > max_irrigationpointwc_id:
                        max_irrigationpointwc_id = irrigationpointwc_id
            if max_irrigationpointwc_id > 0:
                irrigationpointwcswc = self.env['wua.parcel.irrigationpointwc']
                last_irrigationpointwc = \
                    irrigationpointwcswc.browse(max_irrigationpointwc_id)
                if last_irrigationpointwc:
                    last_pos = last_irrigationpointwc.pos
            pos = last_pos + 1
            for irrigationpointwc in vals['irrigationpointwc_ids']:
                irrigationpointwc_oper = irrigationpointwc[0]
                irrigationpointwc_vals = irrigationpointwc[2]
                if irrigationpointwc_oper == 0:
                    irrigationpointwc_vals['irrigationpointwc_code'] = \
                        parcel_name + "-" + \
                        str(pos).zfill(self.SIZE_IRRIGATIONPOINT_SUFFIX)
                    irrigationpointwc_vals['pos'] = pos
                    pos = pos + 1

    def populate_anothercode_pos(self, parcel_name, vals):
        self.populate_irrigationpointwccode_pos(parcel_name, vals)

    def test_other_slave_data(self, vals):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if ('irrigationpointwc_ids' in vals and
           (irrigation_model_type == 0 or irrigation_model_type == 2)):
            correct_waterconnections_no_repeat = \
                self.waterconnections_no_repeat(vals['irrigationpointwc_ids'])
            if not correct_waterconnections_no_repeat:
                raise exceptions.UserError(_('There are repeated water '
                                             'connections.'))
            waterconnections_from_one_hydraulicsector = \
                self.waterconnections_from_one_hydraulicsector(
                    vals['irrigationpointwc_ids'])
            if not waterconnections_from_one_hydraulicsector:
                raise exceptions.UserError(_('The hydraulic sectors '
                                             'are differents.'))
        if ('subparcel_ids' in vals and
           (irrigation_model_type == 1 or irrigation_model_type == 2)):
            correct_irrigationgates_no_repeat = \
                self.irrigationgates_no_repeat(
                    vals['subparcel_ids'])
            if not correct_irrigationgates_no_repeat:
                raise exceptions.UserError(_('There are repeated irrigation '
                                             'gates.'))
            irrigationgates_from_one_irrigationditch = \
                self.irrigationgates_from_one_irrigationditch(
                    vals['subparcel_ids'])
            if not irrigationgates_from_one_irrigationditch:
                raise exceptions.UserError(_('The irrigation ditches '
                                             'are differents.'))
            irrigationgates_in_another_parcel = \
                self.irrigationgates_in_another_parcel(
                    vals['subparcel_ids'])
            if irrigationgates_in_another_parcel:
                raise exceptions.UserError(_('There are some irrigation '
                                             'gates in anoter parcel.'))

    def waterconnections_no_repeat(self, irrigationpointwc_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for irrigationpointwc in irrigationpointwc_ids:
            irrigationpointwc_oper = irrigationpointwc[0]
            irrigationpointwc_id = irrigationpointwc[1]
            irrigationpointwc_vals = irrigationpointwc[2]
            if irrigationpointwc_oper == 4 or (irrigationpointwc_oper == 1 and
               'waterconnection_id' not in irrigationpointwc_vals):
                unchanged_ids.append(irrigationpointwc_id)
            if irrigationpointwc_oper == 0 or (irrigationpointwc_oper == 1 and
               'waterconnection_id' in irrigationpointwc_vals):
                implied_ids.append(
                    irrigationpointwc_vals['waterconnection_id'])
        if len(unchanged_ids) > 0:
            filtered_irrigationpointswc = \
                self.env['wua.parcel.irrigationpointwc'].search(
                    [('id', 'in', unchanged_ids)])
            for irrigationpointwc in filtered_irrigationpointswc:
                implied_ids.append(irrigationpointwc.waterconnection_id.id)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        len_of_implied_ids_original = len(implied_ids)
        if len_of_implied_ids_original > 0:
            implied_ids = list(set(implied_ids))
            len_of_implied_ids_no_repeat = len(implied_ids)
            resp = len_of_implied_ids_original == len_of_implied_ids_no_repeat
        return resp

    def irrigationgates_no_repeat(self, subparcel_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if subparcel_oper == 4 or (subparcel_oper == 1 and
               'irrigationgate_id' not in subparcel_vals):
                unchanged_ids.append(subparcel_id)
            if subparcel_oper == 0 or (subparcel_oper == 1 and
               'irrigationgate_id' in subparcel_vals):
                implied_ids.append(subparcel_vals['irrigationgate_id'])
        if len(unchanged_ids) > 0:
            filtered_subparcels = \
                self.env['wua.parcel.subparcel'].search(
                    [('id', 'in', unchanged_ids)])
            for subparcel in filtered_subparcels:
                implied_ids.append(subparcel.irrigationgate_id.id)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        len_of_implied_ids_original = len(implied_ids)
        if len_of_implied_ids_original > 0:
            implied_ids = list(set(implied_ids))
            len_of_implied_ids_no_repeat = len(implied_ids)
            resp = len_of_implied_ids_original == len_of_implied_ids_no_repeat
        return resp

    def waterconnections_from_one_hydraulicsector(self, irrigationpointwc_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for irrigationpointwc in irrigationpointwc_ids:
            irrigationpointwc_oper = irrigationpointwc[0]
            irrigationpointwc_id = irrigationpointwc[1]
            irrigationpointwc_vals = irrigationpointwc[2]
            if irrigationpointwc_oper == 4 or (irrigationpointwc_oper == 1 and
               'waterconnection_id' not in irrigationpointwc_vals):
                unchanged_ids.append(irrigationpointwc_id)
            if irrigationpointwc_oper == 0 or (irrigationpointwc_oper == 1 and
               'waterconnection_id' in irrigationpointwc_vals):
                implied_ids.append(
                    irrigationpointwc_vals['waterconnection_id'])
        if len(unchanged_ids) > 0:
            filtered_irrigationpointswc = \
                self.env['wua.parcel.irrigationpointwc'].search(
                    [('id', 'in', unchanged_ids)])
            for irrigationpointwc in filtered_irrigationpointswc:
                implied_ids.append(irrigationpointwc.waterconnection_id.id)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        filtered_waterconnections = \
            self.env['wua.waterconnection'].search(
                [('id', 'in', implied_ids)])
        hydraulicsector_id = 0
        for waterconnection in filtered_waterconnections:
            if waterconnection.hydraulicsector_id.id != hydraulicsector_id:
                if hydraulicsector_id == 0:
                    hydraulicsector_id = waterconnection.hydraulicsector_id.id
                else:
                    resp = False
                    break
        return resp

    def irrigationgates_from_one_irrigationditch(self, subparcel_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if subparcel_oper == 4 or (subparcel_oper == 1 and
               'irrigationgate_id' not in subparcel_vals):
                unchanged_ids.append(subparcel_id)
            if subparcel_oper == 0 or (subparcel_oper == 1 and
               'irrigationgate_id' in subparcel_vals):
                implied_ids.append(subparcel_vals['irrigationgate_id'])
        if len(unchanged_ids) > 0:
            filtered_subparcels = \
                self.env['wua.parcel.subparcel'].search(
                    [('id', 'in', unchanged_ids)])
            for subparcel in filtered_subparcels:
                implied_ids.append(subparcel.irrigationgate_id.id)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        filtered_irrigationgates = \
            self.env['wua.irrigationgate'].search(
                [('id', 'in', implied_ids)])
        irrigationditch_id = 0
        for irrigationgate in filtered_irrigationgates:
            if irrigationgate.irrigationditch_id.id != irrigationditch_id:
                if irrigationditch_id == 0:
                    irrigationditch_id = irrigationgate.irrigationditch_id.id
                else:
                    resp = False
                    break
        return resp

    def irrigationgates_in_another_parcel(self, subparcel_ids):
        implied_ids = []
        unchanged_ids = []
        parcel_id = None
        if self.id:
            parcel_id = self.id
        for subparcel in subparcel_ids:
            subparcel_oper = subparcel[0]
            subparcel_id = subparcel[1]
            subparcel_vals = subparcel[2]
            if subparcel_oper == 4 or (subparcel_oper == 1 and
               'irrigationgate_id' not in subparcel_vals):
                unchanged_ids.append(subparcel_id)
            if subparcel_oper == 0 or (subparcel_oper == 1 and
               'irrigationgate_id' in subparcel_vals):
                implied_ids.append(subparcel_vals['irrigationgate_id'])
            if parcel_id is None and 'parcel_id' in subparcel_vals:
                parcel_id = subparcel_vals['parcel_id']
        if len(unchanged_ids) > 0:
            filtered_subparcels = \
                self.env['wua.parcel.subparcel'].search(
                    [('id', 'in', unchanged_ids)])
            for subparcel in filtered_subparcels:
                implied_ids.append(subparcel.irrigationgate_id.id)
        implied_ids = filter(lambda x: x != 0, implied_ids)
        other_subparcels = self.env['wua.parcel.subparcel'].search(
            [('irrigationgate_id', 'in', implied_ids),
             ('parcel_id', '!=', parcel_id)])
        resp = len(other_subparcels) > 0
        return resp

    def do_process_active_field(self, active):
        super(WuaParcel, self).do_process_active_field(active)
        parcel_id = self.id
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].with_context(
            active_test=False)
        filtered_irrigationpoints = irrigationpoints.search(
            [('parcel_id', '=', parcel_id)])
        for irrigationpoint in filtered_irrigationpoints:
            irrigationpoint.active = active
        irrigationpointswc = self.env['wua.parcel.irrigationpointwc'].\
            with_context(active_test=False)
        filtered_irrigationpointswc = irrigationpointswc.search(
            [('parcel_id', '=', parcel_id)])
        for irrigationpointwc in filtered_irrigationpointswc:
            irrigationpointwc.active = active

    @api.multi
    def unlink(self):
        # if a parcel is deleted, its irrigation points are deleted
        # "in cascade". Then the ORM do not work, so it is necessary
        # to delete manually beforehand (otherwise, the number of parcels
        # in the water connections will not be updated correctly).
        for record in self:
            irrigationpoints_to_del = \
                self.env['wua.parcel.irrigationpoint'].search(
                    [('parcel_id', '=', record.id)])
            irrigationpoints_to_del.unlink()
        return super(WuaParcel, self).unlink()

    def recalculate_irrigationpoints(self):
        self.env['wua.parcel.irrigationpoint'].search([]).unlink()
        subparcels = self.env['wua.parcel.subparcel'].search(
            [('irrigationgate_id', '!=', False)])
        irrigation_points_wc = self.env['wua.parcel.irrigationpointwc'].search(
            [])
        irrigation_points = self.env['wua.parcel.irrigationpoint']
        for subparcel in subparcels:
            parcel_id = subparcel.parcel_id.id
            irrigationgate_id = subparcel.irrigationgate_id.id
            irrigation_points.create({
                'parcel_id': parcel_id,
                'type': 'IG',
                'irrigationgate_id': irrigationgate_id,
                })
        for irrigation_point_wc in irrigation_points_wc:
            parcel_id = irrigation_point_wc.parcel_id.id
            waterconnection_id = irrigation_point_wc.waterconnection_id.id
            irrigation_points.create({
                'parcel_id': parcel_id,
                'type': 'WC',
                'waterconnection_id': waterconnection_id,
                })

    @api.multi
    def action_global_irrigationpoints_calculation(self):
        res_model = 'wua.hydraulicsector'
        name = _('Hydraulic Sectors')
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 1:
            res_model = 'wua.irrigationditch'
            name = _('Irrigation Ditches')
        self.recalculate_irrigationpoints()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
        return act_window


class WuaParcelIrrigationpoint(models.Model):
    _name = 'wua.parcel.irrigationpoint'
    _description = 'Irrigation point of a parcel'
    _order = 'parcel_id, type, name'

    SIZE_NAME = 25

    @api.model
    def default_get(self, fields):
        res = super(WuaParcelIrrigationpoint, self).default_get(fields)
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            res['type'] = 'WC'
        if irrigation_model_type == 1:
            res['type'] = 'IG'
        return res

    name = fields.Char(
        string='Irrigation Point Name',
        size=SIZE_NAME,
        index=True,
        readonly=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    type = fields.Selection([
        ('WC', 'Water Connection'),
        ('IG', 'Irrigation Gate'),
        ],
        default='WC',
        string='Type',
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection Id.',
        comodel_name='wua.waterconnection',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_irrigationshed_id',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulicsector_id',
        ondelete='restrict')

    irrigationgate_id = fields.Many2one(
        string='Irrigation Gate Id.',
        comodel_name='wua.irrigationgate',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        store=True,
        compute='_compute_irrigationditch_id',
        ondelete='restrict')

    parcel_rural_location_county = fields.Char(
        string='Location',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_from_parcel_id')

    parcel_area_official_hec = fields.Float(
        string='Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec_from_parcel_id')

    parcel_cadastral_reference = fields.Char(
        string='Cadastral Reference',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_cadastral_polygon = fields.Char(
        string='Polygon',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_cadastral_parcel = fields.Char(
        string='Parcel',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_street_view_link = fields.Char(
        string='Street View',
        compute='_compute_calculated_data_from_parcel_id')

    parcel_gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_calculated_data_from_parcel_id')

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            if record.waterconnection_id:
                record.irrigationshed_id =\
                    record.waterconnection_id.irrigationshed_id
            else:
                record.irrigationshed_id = None

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            if record.waterconnection_id:
                record.hydraulicsector_id =\
                    record.waterconnection_id.hydraulicsector_id
            else:
                record.hydraulicsector_id = None

    @api.depends('irrigationgate_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            if record.irrigationgate_id:
                record.irrigationditch_id =\
                    record.irrigationgate_id.irrigationditch_id
            else:
                record.irrigationditch_id = None

    @api.multi
    def _compute_calculated_data_from_parcel_id(self):
        for record in self:
            parcel = record.parcel_id
            if parcel:
                record.parcel_rural_location_county = \
                    parcel.rural_location_county
                record.parcel_cadastral_reference = parcel.cadastral_reference
                record.parcel_cadastral_polygon = parcel.cadastral_polygon
                record.parcel_cadastral_parcel = parcel.cadastral_parcel
                record.parcel_cadastral_reference_link = \
                    parcel.cadastral_reference_link
                record.parcel_street_view_link = \
                    parcel.street_view_link
                record.parcel_gis_viewer_link = \
                    parcel.gis_viewer_link

    @api.depends('parcel_id.area_official')
    def _compute_area_official_from_parcel_id(self):
        irrigationpoint_recordset = []
        if len(self) == 1:
            irrigationpoint_recordset = [self]
        else:
            irrigationpoint_recordset = self
        for irrigationpoint in irrigationpoint_recordset:
            parcel = irrigationpoint.parcel_id
            if parcel:
                irrigationpoint.parcel_area_official = parcel.area_official

    @api.depends('parcel_id.area_official_hec')
    def _compute_area_official_hec_from_parcel_id(self):
        irrigationpoint_recordset = []
        if len(self) == 1:
            irrigationpoint_recordset = [self]
        else:
            irrigationpoint_recordset = self
        for irrigationpoint in irrigationpoint_recordset:
            parcel = irrigationpoint.parcel_id
            if parcel:
                irrigationpoint.parcel_area_official_hec = \
                    parcel.area_official_hec

    @api.constrains('waterconnection_id')
    def _check_waterconnection_id(self):
        if self.type == 'IG' and int(self.waterconnection_id.id > 0):
            raise exceptions.ValidationError(_('Incompatible irrigation ' +
                                               'point type.'))

    @api.constrains('irrigationgate_id')
    def _check_irrigationgate_id(self):
        if self.type == 'WC' and int(self.irrigationgate_id.id > 0):
            raise exceptions.ValidationError(_('Incompatible irrigation ' +
                                               'point type.'))

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'WC':
            self.irrigationgate_id = None
        if self.type == 'IG':
            self.waterconnection_id = None

    @api.model
    def create(self, vals):
        id_waterconnection = 0
        id_irrigationgate = 0
        if 'waterconnection_id' in vals:
            id_waterconnection = int(vals['waterconnection_id'])
        if 'irrigationgate_id' in vals:
            id_irrigationgate = int(vals['irrigationgate_id'])
        if id_waterconnection == 0 and id_irrigationgate == 0:
            raise exceptions.ValidationError(_('Empty Irrigation Point.'))
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'wua.parcel.irrigationpoint')
        return super(WuaParcelIrrigationpoint, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'waterconnection_id' in vals or 'irrigationgate_id' in vals:
            irrigation_type = self.type
            id_waterconnection = self.waterconnection_id.id
            id_irrigationgate = self.irrigationgate_id.id
            if 'type' in vals:
                irrigation_type = vals['type']
            if 'waterconnection_id' in vals:
                id_waterconnection = int(vals['waterconnection_id'])
            if 'irrigationgate_id' in vals:
                id_irrigationgate = int(vals['irrigationgate_id'])
            if (irrigation_type == 'WC' and id_waterconnection == 0) or \
               (irrigation_type == 'IG' and id_irrigationgate == 0):
                raise exceptions.ValidationError(_('Empty Irrigation Point.'))
        super(WuaParcelIrrigationpoint, self).write(vals)
        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcelIrrigationpoint, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_tree(doc)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_search(doc)
        return res

    def fields_view_get_tree(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            for node in doc.xpath(
                    "//field[@name='irrigationgate_id']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "tree_invisible": true}')
            for node in doc.xpath(
                    "//field[@name='irrigationditch_id']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "tree_invisible": true}')
        if irrigation_model_type == 1:
            for node in doc.xpath(
                    "//field[@name='waterconnection_id']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "tree_invisible": true}')
            for node in doc.xpath(
                    "//field[@name='irrigationshed_id']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "tree_invisible": true}')
            for node in doc.xpath(
                    "//field[@name='hydraulicsector_id']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "tree_invisible": true}')
        return etree.tostring(doc)

    def fields_view_get_search(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            self.fields_view_get_search_irrigation_model_type_0(doc)
        if irrigation_model_type == 1:
            self.fields_view_get_search_irrigation_model_type_1(doc)
        if irrigation_model_type != 2:
            for node in doc.xpath(
                    "//filter[@name='waterconnection']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
            for node in doc.xpath(
                    "//filter[@name='irrigationgate']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        return etree.tostring(doc)

    def fields_view_get_search_irrigation_model_type_0(self, doc):
        for node in doc.xpath(
                "//field[@name='irrigationgate_id']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='irrigationditch_id']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='irrigationditch']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')

    def fields_view_get_search_irrigation_model_type_1(self, doc):
        for node in doc.xpath(
                "//field[@name='waterconnection_id']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='irrigationshed_id']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//field[@name='hydraulicsector_id']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='hydraulicsector']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')
        for node in doc.xpath(
                "//filter[@name='irrigationshed']"):
            node.set('invisible', '1')
            node.set('modifiers',
                     '{"readonly": true, "invisible": true}')

    @api.multi
    def action_see_cadastral_report(self):
        self.ensure_one()
        if self.parcel_cadastral_reference_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.parcel_cadastral_reference_link,
                'target': 'new',
            }

    @api.multi
    def action_see_street_view(self):
        self.ensure_one()
        if self.parcel_street_view_link:
            url_gis_viewer_epsg_code = self.env['ir.values'].get_default(
                'wua.configuration', 'url_gis_viewer_epsg_code')
            if url_gis_viewer_epsg_code:
                epsg_code = 'epsg:' + str(url_gis_viewer_epsg_code)
                url = self.parcel_street_view_link
                in_proj = Proj(init=epsg_code)
                out_proj = Proj(init='epsg:4326')
                x_in = self.parcel_id.street_view_x
                y_in = self.parcel_id.street_view_y
                x_out, y_out = transform(in_proj, out_proj, x_in, y_in)
                xc = str(x_out)
                yc = str(y_out)
                url = url.replace("ycval", yc)
                url = url.replace("xcval", xc)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                    }

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.parcel_gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.parcel_gis_viewer_link,
                'target': 'new',
            }


class WuaParcelSubparcel(models.Model):
    _inherit = 'wua.parcel.subparcel'

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_hydraulicsector_id')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_irrigationditch_id')

    irrigationgate_id = fields.Many2one(
        string='Irrigation Gate',
        comodel_name='wua.irrigationgate',
        ondelete='restrict')

    irrigation_duration_coefficient = fields.Float(
        string='Irrigation Coef.',
        digits=(4, 2),
        required=True,
        default=1)

    _sql_constraints = [
        ('valid_irrigation_duration_coefficient',
         'CHECK (irrigation_duration_coefficient >= 0)',
         'The irrigation coefficient must be a value zero or positive.')]

    @api.depends('parcel_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.parcel_id.hydraulicsector_id

    @api.depends('parcel_id.irrigationditch_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            record.irrigationditch_id = record.parcel_id.irrigationditch_id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcelSubparcel, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_search(doc)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            res['arch'] = self.fields_view_get_tree(doc)
        return res

    def fields_view_get_search(self, doc):
        irrigation_model_type = int(self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'irrigation_model_type'))
        if irrigation_model_type == 0:
            for node in doc.xpath(
                    "//filter[@name='irrigationditch']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        if irrigation_model_type == 1:
            for node in doc.xpath(
                    "//filter[@name='hydraulicsector']"):
                node.set('invisible', '1')
                node.set('modifiers',
                         '{"readonly": true, "invisible": true}')
        return etree.tostring(doc)

    def fields_view_get_tree(self, doc):
        if (self.env.context.get('tree_view_ref') ==
           'base_wua.wua_edit_parcel_subparcel_view_tree'):
            irrigation_model_type = int(self.env['ir.values'].get_default(
                'wua.infrastructure.configuration', 'irrigation_model_type'))
            if irrigation_model_type == 0:
                for node in doc.xpath(
                        "//field[@name='irrigationgate_id']"):
                    node.set('invisible', '1')
                    node.set('modifiers',
                             '{"readonly": true, "tree_invisible": true}')
                for node in doc.xpath(
                        "//field[@name='irrigation_duration_coefficient']"):
                    node.set('invisible', '1')
                    node.set('modifiers',
                             '{"readonly": true, "tree_invisible": true}')
        return etree.tostring(doc)


class WuaParcelIrrigationpointWC(models.Model):
    _name = 'wua.parcel.irrigationpointwc'
    _description = 'Irrigation point of a parcel (WC)'
    _order = 'irrigationpointwc_code'

    SIZE_NAME = 25

    name = fields.Char(
        string='Irrigation Point (WC) Name',
        size=SIZE_NAME,
        index=True,
        readonly=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    irrigationpointwc_code = fields.Char(
        string='Irrigation Point (WC) Code',
        size=SIZE_NAME,
        index=True)

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Irrigation Point',
        required=True,
        default=0)

    pos_str = fields.Char(
        string='Number',
        compute='_compute_pos_str')

    waterconnection_id = fields.Many2one(
        string='Water Connection Id.',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_irrigationshed_id',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulicsector_id',
        ondelete='restrict')

    @api.multi
    def _compute_pos_str(self):
        for record in self:
            pos = record.pos
            if pos:
                record.pos_str = str(pos)
            else:
                record.pos_str = ''

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            if record.waterconnection_id:
                record.irrigationshed_id =\
                    record.waterconnection_id.irrigationshed_id
            else:
                record.irrigationshed_id = None

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            if record.waterconnection_id:
                record.hydraulicsector_id =\
                    record.waterconnection_id.hydraulicsector_id
            else:
                record.hydraulicsector_id = None

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'wua.parcel.irrigationpointwc')
        return super(WuaParcelIrrigationpointWC, self).create(vals)
