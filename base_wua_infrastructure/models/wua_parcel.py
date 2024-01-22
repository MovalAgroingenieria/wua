# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from pyproj import Proj, transform
from odoo import models, fields, api,  exceptions, _


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
        default=True,
        track_visibility='onchange')

    gravityfed_irrigation_right = fields.Boolean(
        string="Water Right (grav)",
        default=True,
        track_visibility='onchange')

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

    with_pumping = fields.Boolean(
        string='With pumping',
        store=True,
        compute='_compute_with_pumping')

    supply_suspended = fields.Boolean(
        string='Supply suspended',
        default=False)

    number_of_waterpayers = fields.Integer(
        string='Number of water payers',
        compute='_compute_number_of_waterpayers')

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

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.hydraulicsector_id')
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

    @api.multi
    def _compute_number_of_waterpayers(self):
        for record in self:
            number_of_waterpayers = 0
            self.env.cr.execute("""
                SELECT COUNT(*) FROM wua_parcel_partnerlink
                WHERE active AND parcel_id=%s AND
                water_costs_percentage > 0""", (record.id,))
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('count') is not None:
                number_of_waterpayers = query_results[0].get('count')
            record.number_of_waterpayers = number_of_waterpayers

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

    def check_gis_irrigationshed_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_irrigationshed')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_irrigationshed_table(self):
        # Check if wua gis table already exists
        gis_irrigationshed_table_created = \
            self.check_gis_irrigationshed_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis irrigationshed don't
        if (not gis_irrigationshed_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_irrigationshed_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_irrigationshed
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_irrigationshed_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_irrigationshed_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_irrigationshed_idx ON public.wua_gis_irrigationshed
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_irrigationshed_triggers(self):
        gis_irrigationshed_table_created = \
            self.check_gis_irrigationshed_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_irrigationshed_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_irrigationshed data when the
            # wua_gis_irrigationshed table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_irrigationshed_update_on_wua_irrigationshed()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_irrigationshed SET
                        with_gis_irrigationshed = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_irrigationshed SET
                        with_gis_irrigationshed = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis irrigationshed is
            # unlinked and other when a gis irrigationshed is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_irrigationshed_write_trigger ON
                    public.wua_gis_irrigationshed;
                DROP TRIGGER IF EXISTS
                    wua_gis_irrigationshed_create_unlink_trigger ON
                    public.wua_gis_irrigationshed;

                CREATE TRIGGER wua_gis_irrigationshed_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_irrigationshed FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_irrigationshed_update_on_wua_irrigationshed();

                CREATE TRIGGER wua_gis_irrigationshed_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_irrigationshed FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_irrigationshed_update_on_wua_irrigationshed();
            """)
            self.env.cr.commit()
            # Function that will update the wua_irrigationshed data when the
            # wua_irrigationshed table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_irrigationshed_update_on_wua_irrigationshed() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_irrigationshed SET
                        with_gis_irrigationshed = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_irrigationshed)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_irrigationshed WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_irrigationshed WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the irrigationshed is created
            # and other when a gis irrigationshed is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_irrigationshed_write_trigger ON
                    public.wua_irrigationshed;
                DROP TRIGGER IF EXISTS wua_irrigationshed_create_trigger ON
                    public.wua_irrigationshed;

                CREATE TRIGGER wua_irrigationshed_write_trigger
                AFTER UPDATE OF name ON
                public.wua_irrigationshed FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_irrigationshed_update_on_wua_irrigationshed();

                CREATE TRIGGER wua_irrigationshed_create_trigger
                AFTER INSERT ON
                public.wua_irrigationshed FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_irrigationshed_update_on_wua_irrigationshed();
            """)
            self.env.cr.commit()

    def check_gis_flowdivider_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_flowdivider')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_flowdivider_table(self):
        # Check if wua gis table already exists
        gis_flowdivider_table_created = \
            self.check_gis_flowdivider_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis flowdivider don't
        if (not gis_flowdivider_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_flowdivider_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_flowdivider
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_flowdivider_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_flowdivider_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_flowdivider_idx ON public.wua_gis_flowdivider
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_flowdivider_triggers(self):
        gis_flowdivider_table_created = \
            self.check_gis_flowdivider_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_flowdivider_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_flowdivider data when the
            # wua_gis_flowdivider table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_flowdivider_update_on_wua_flowdivider()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_flowdivider SET
                        with_gis_flowdivider = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_flowdivider SET
                        with_gis_flowdivider = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis flowdivider is
            # unlinked and other when a gis flowdivider is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_flowdivider_write_trigger ON
                    public.wua_gis_flowdivider;
                DROP TRIGGER IF EXISTS
                    wua_gis_flowdivider_create_unlink_trigger ON
                    public.wua_gis_flowdivider;

                CREATE TRIGGER wua_gis_flowdivider_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_flowdivider FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_flowdivider_update_on_wua_flowdivider();

                CREATE TRIGGER wua_gis_flowdivider_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_flowdivider FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_flowdivider_update_on_wua_flowdivider();
            """)
            self.env.cr.commit()
            # Function that will update the wua_flowdivider data when the
            # wua_flowdivider table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_flowdivider_update_on_wua_flowdivider() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_flowdivider SET
                        with_gis_flowdivider = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_flowdivider)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_flowdivider WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_flowdivider WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the flowdivider is created
            # and other when a gis flowdivider is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_flowdivider_write_trigger ON
                    public.wua_flowdivider;
                DROP TRIGGER IF EXISTS wua_flowdivider_create_trigger ON
                    public.wua_flowdivider;

                CREATE TRIGGER wua_flowdivider_write_trigger
                AFTER UPDATE OF name ON
                public.wua_flowdivider FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_flowdivider_update_on_wua_flowdivider();

                CREATE TRIGGER wua_flowdivider_create_trigger
                AFTER INSERT ON
                public.wua_flowdivider FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_flowdivider_update_on_wua_flowdivider();
            """)
            self.env.cr.commit()

    def check_gis_irrigationditch_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_irrigationditch')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_irrigationditch_table(self):
        # Check if wua gis table already exists
        gis_irrigationditch_table_created = \
            self.check_gis_irrigationditch_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis irrigationditch don't
        if (not gis_irrigationditch_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_irrigationditch_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_irrigationditch
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_irrigationditch_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(MultiLineString,25830),
                        code bigint,
                        level integer,
                        UNIQUE(code),
                        CONSTRAINT wua_gis_irrigationditch_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_irrigationditch_idx ON public.wua_gis_irrigationditch
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_irrigationditch_triggers(self):
        gis_irrigationditch_table_created = \
            self.check_gis_irrigationditch_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_irrigationditch_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_irrigationditch data when the
            # wua_gis_irrigationditch table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_irrigationditch_update_on_wua_irrigationditch()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_irrigationditch SET
                        with_gis_irrigationditch = False
                    WHERE irrigationditch_code = OLD.code;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_irrigationditch SET
                        with_gis_irrigationditch = True
                    WHERE irrigationditch_code = NEW.code;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis irrigationditch is
            # unlinked and other when a gis irrigationditch is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_irrigationditch_write_trigger ON
                    public.wua_gis_irrigationditch;
                DROP TRIGGER IF EXISTS
                    wua_gis_irrigationditch_create_unlink_trigger ON
                    public.wua_gis_irrigationditch;

                CREATE TRIGGER wua_gis_irrigationditch_write_trigger
                AFTER UPDATE OF code ON
                public.wua_gis_irrigationditch FOR EACH ROW WHEN
                (OLD.code IS DISTINCT FROM NEW.code)
                EXECUTE PROCEDURE
                    wua_gis_irrigationditch_update_on_wua_irrigationditch();

                CREATE TRIGGER wua_gis_irrigationditch_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_irrigationditch FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_irrigationditch_update_on_wua_irrigationditch();
            """)
            self.env.cr.commit()
            # Function that will update the wua_irrigationditch data when the
            # wua_irrigationditch table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_irrigationditch_update_on_wua_irrigationditch() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_irrigationditch SET with_gis_irrigationditch =
                    (SELECT NEW.irrigationditch_code IN
                        (SELECT code FROM wua_gis_irrigationditch))
                    WHERE irrigationditch_code = NEW.irrigationditch_code;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the irrigationditch is created
            # and other when a gis irrigationditch is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_irrigationditch_write_trigger ON
                    public.wua_irrigationditch;
                DROP TRIGGER IF EXISTS wua_irrigationditch_create_trigger ON
                    public.wua_irrigationditch;

                CREATE TRIGGER wua_irrigationditch_write_trigger
                AFTER UPDATE OF irrigationditch_code ON
                public.wua_irrigationditch FOR EACH ROW WHEN
                (OLD.irrigationditch_code IS DISTINCT FROM
                    NEW.irrigationditch_code)
                EXECUTE PROCEDURE
                    wua_irrigationditch_update_on_wua_irrigationditch();

                CREATE TRIGGER wua_irrigationditch_create_trigger
                AFTER INSERT ON
                public.wua_irrigationditch FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_irrigationditch_update_on_wua_irrigationditch();
            """)
            self.env.cr.commit()

    # Airvalve
    def check_gis_airvalve_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_airvalve')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_airvalve_table(self):
        # Check if wua gis table already exists
        gis_airvalve_table_created = \
            self.check_gis_airvalve_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis airvalve don't
        if (not gis_airvalve_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_airvalve_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_airvalve
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_airvalve_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_airvalve_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_airvalve_idx ON public.wua_gis_airvalve
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_airvalve_triggers(self):
        gis_airvalve_table_created = \
            self.check_gis_airvalve_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_airvalve_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_airvalve data when the
            # wua_gis_airvalve table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_airvalve_update_on_wua_airvalve()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_airvalve SET
                        with_gis_airvalve = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_airvalve SET
                        with_gis_airvalve = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis airvalve is
            # unlinked and other when a gis airvalve is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_airvalve_write_trigger ON
                    public.wua_gis_airvalve;
                DROP TRIGGER IF EXISTS
                    wua_gis_airvalve_create_unlink_trigger ON
                    public.wua_gis_airvalve;

                CREATE TRIGGER wua_gis_airvalve_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_airvalve FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_airvalve_update_on_wua_airvalve();

                CREATE TRIGGER wua_gis_airvalve_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_airvalve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_airvalve_update_on_wua_airvalve();
            """)
            self.env.cr.commit()
            # Function that will update the wua_airvalve data when the
            # wua_airvalve table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_airvalve_update_on_wua_airvalve() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_airvalve SET
                        with_gis_airvalve = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_airvalve)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_airvalve WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_airvalve WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the airvalve is created
            # and other when a gis airvalve is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_airvalve_write_trigger ON
                    public.wua_airvalve;
                DROP TRIGGER IF EXISTS wua_airvalve_create_trigger ON
                    public.wua_airvalve;

                CREATE TRIGGER wua_airvalve_write_trigger
                AFTER UPDATE OF name ON
                public.wua_airvalve FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_airvalve_update_on_wua_airvalve();

                CREATE TRIGGER wua_airvalve_create_trigger
                AFTER INSERT ON
                public.wua_airvalve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_airvalve_update_on_wua_airvalve();
            """)
            self.env.cr.commit()

    # Valve
    def check_gis_valve_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_valve')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_valve_table(self):
        # Check if wua gis table already exists
        gis_valve_table_created = \
            self.check_gis_valve_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis valve don't
        if (not gis_valve_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_valve_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_valve
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_valve_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_valve_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_valve_idx ON public.wua_gis_valve
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_valve_triggers(self):
        gis_valve_table_created = \
            self.check_gis_valve_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_valve_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_valve data when the
            # wua_gis_valve table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_valve_update_on_wua_valve()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_valve SET
                        with_gis_valve = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_valve SET
                        with_gis_valve = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis valve is
            # unlinked and other when a gis valve is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_valve_write_trigger ON
                    public.wua_gis_valve;
                DROP TRIGGER IF EXISTS
                    wua_gis_valve_create_unlink_trigger ON
                    public.wua_gis_valve;

                CREATE TRIGGER wua_gis_valve_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_valve FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_valve_update_on_wua_valve();

                CREATE TRIGGER wua_gis_valve_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_valve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_valve_update_on_wua_valve();
            """)
            self.env.cr.commit()
            # Function that will update the wua_valve data when the
            # wua_valve table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_valve_update_on_wua_valve() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_valve SET
                        with_gis_valve = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_valve)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_valve WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_valve WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the valve is created
            # and other when a gis valve is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_valve_write_trigger ON
                    public.wua_valve;
                DROP TRIGGER IF EXISTS wua_valve_create_trigger ON
                    public.wua_valve;

                CREATE TRIGGER wua_valve_write_trigger
                AFTER UPDATE OF name ON
                public.wua_valve FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_valve_update_on_wua_valve();

                CREATE TRIGGER wua_valve_create_trigger
                AFTER INSERT ON
                public.wua_valve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_valve_update_on_wua_valve();
            """)
            self.env.cr.commit()

    # DraingeValve
    def check_gis_drainagevalve_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_drainagevalve')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_wua_gis_drainagevalve_table(self):
        # Check if wua gis table already exists
        gis_drainagevalve_table_created = \
            self.check_gis_drainagevalve_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis drainagevalve don't
        if (not gis_drainagevalve_table_created and
                extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS
                    public.wua_gis_drainagevalve_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_drainagevalve
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_drainagevalve_gid_seq'::regclass),
                        name character varying(254)
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(Point,25830),
                        UNIQUE(name),
                        CONSTRAINT wua_gis_drainagevalve_pkey
                            PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_drainagevalve_idx ON public.wua_gis_drainagevalve
                    USING gist (geom);
            """)
            self.env.cr.commit()

    def create_drainagevalve_triggers(self):
        gis_drainagevalve_table_created = \
            self.check_gis_drainagevalve_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_drainagevalve_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_drainagevalve data when the
            # wua_gis_drainagevalve table has some change, (Create, Update or
            # Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_drainagevalve_update_on_wua_drainagevalve()
                    RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_drainagevalve SET
                        with_gis_drainagevalve = False,
                        gis_viewer_x = 0,
                        gis_viewer_y = 0
                    WHERE name = OLD.name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_drainagevalve SET
                        with_gis_drainagevalve = True,
                        gis_viewer_x = postgis.ST_X(NEW.geom)::INTEGER,
                        gis_viewer_y = postgis.ST_Y(NEW.geom)::INTEGER
                    WHERE name = NEW.name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis drainagevalve is
            # unlinked and other when a gis drainagevalve is created or
            # updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_drainagevalve_write_trigger ON
                    public.wua_gis_drainagevalve;
                DROP TRIGGER IF EXISTS
                    wua_gis_drainagevalve_create_unlink_trigger ON
                    public.wua_gis_drainagevalve;

                CREATE TRIGGER wua_gis_drainagevalve_write_trigger
                AFTER UPDATE OF name, geom ON
                public.wua_gis_drainagevalve FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                 OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_gis_drainagevalve_update_on_wua_drainagevalve();

                CREATE TRIGGER wua_gis_drainagevalve_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_drainagevalve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_gis_drainagevalve_update_on_wua_drainagevalve();
            """)
            self.env.cr.commit()
            # Function that will update the wua_drainagevalve data when the
            # wua_drainagevalve table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_drainagevalve_update_on_wua_drainagevalve() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                    UPDATE public.wua_drainagevalve SET
                        with_gis_drainagevalve = (SELECT NEW.name IN
                            (SELECT name FROM wua_gis_drainagevalve)),
                        gis_viewer_x = (SELECT postgis.ST_X(geom)::INTEGER FROM
                            wua_gis_drainagevalve WHERE name = NEW.name
                            LIMIT 1),
                        gis_viewer_y = (SELECT postgis.ST_Y(geom)::INTEGER FROM
                            wua_gis_drainagevalve WHERE name = NEW.name
                            LIMIT 1)
                    WHERE name = NEW.name;
                RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the drainagevalve is created
            # and other when a gis drainagevalve is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_drainagevalve_write_trigger ON
                    public.wua_drainagevalve;
                DROP TRIGGER IF EXISTS wua_drainagevalve_create_trigger ON
                    public.wua_drainagevalve;

                CREATE TRIGGER wua_drainagevalve_write_trigger
                AFTER UPDATE OF name ON
                public.wua_drainagevalve FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_drainagevalve_update_on_wua_drainagevalve();

                CREATE TRIGGER wua_drainagevalve_create_trigger
                AFTER INSERT ON
                public.wua_drainagevalve FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_drainagevalve_update_on_wua_drainagevalve();
            """)
            self.env.cr.commit()

    def set_gis_fields_irrigationshed(self):
        gis_irrigationshed_ok = self.check_gis_irrigationshed_created()
        if (gis_irrigationshed_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_irrigationshed
                    SET with_gis_irrigationshed = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_irrigationshed wi1
                    SET with_gis_irrigationshed = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_irrigationshed wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_irrigationshed_ok = False
        return gis_irrigationshed_ok

    def set_gis_fields_flowdivider(self):
        gis_flowdivider_ok = self.check_gis_flowdivider_created()
        if (gis_flowdivider_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_flowdivider
                    SET with_gis_flowdivider = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_flowdivider wi1
                    SET with_gis_flowdivider = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_flowdivider wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_flowdivider_ok = False
        return gis_flowdivider_ok

    def set_gis_fields_irrigationditch(self):
        gis_irrigationditch_ok = self.check_gis_irrigationditch_created()
        if gis_irrigationditch_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_irrigationditch
                    SET with_gis_irrigationditch = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_irrigationditch wi1
                    SET with_gis_irrigationditch = TRUE
                    FROM public.wua_gis_irrigationditch wgi1 WHERE
                        wi1.irrigationditch_code = wgi1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_irrigationditch_ok = False
        return gis_irrigationditch_ok

    def set_gis_fields_airvalve(self):
        gis_airvalve_ok = self.check_gis_airvalve_created()
        if (gis_airvalve_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_airvalve
                    SET with_gis_airvalve = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_airvalve wi1
                    SET with_gis_airvalve = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_airvalve wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_airvalve_ok = False
        return gis_airvalve_ok

    def set_gis_fields_valve(self):
        gis_valve_ok = self.check_gis_valve_created()
        if (gis_valve_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_valve
                    SET with_gis_valve = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_valve wi1
                    SET with_gis_valve = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_valve wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_valve_ok = False
        return gis_valve_ok

    def set_gis_fields_drainagevalve(self):
        gis_drainagevalve_ok = self.check_gis_drainagevalve_created()
        if (gis_drainagevalve_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_drainagevalve
                    SET with_gis_drainagevalve = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_drainagevalve wi1
                    SET with_gis_drainagevalve = TRUE,
                        gis_viewer_x = postgis.ST_X(wgi1.geom),
                        gis_viewer_y = postgis.ST_Y(wgi1.geom)
                    FROM public.wua_gis_draiangevalve wgi1 WHERE
                        wi1.name = wgi1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_drainagevalve_ok = False
        return gis_drainagevalve_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # Irrigationshed GIS
        gis_irrigationshed_ok = self.set_gis_fields_irrigationshed()
        # Flowdivider GIS
        gis_flowdivider_ok = self.set_gis_fields_flowdivider()
        # Irrigationditch GIS
        gis_irrigationditch_ok = self.set_gis_fields_irrigationditch()
        # airvalve GIS
        gis_airvalve_ok = self.set_gis_fields_airvalve()
        # valve GIS
        gis_valve_ok = self.set_gis_fields_valve()
        # drainagevalve GIS
        gis_drainagevalve_ok = self.set_gis_fields_drainagevalve()
        return gis_parcels_ok and gis_irrigationshed_ok and \
            gis_irrigationditch_ok and gis_airvalve_ok and gis_valve_ok and \
            gis_drainagevalve_ok and gis_flowdivider_ok

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
        check_wcs_diff_sector = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'check_waterconnections_different_hydraulic_sectors')
        if ('irrigationpointwc_ids' in vals and
           (irrigation_model_type == 0 or irrigation_model_type == 2)):
            correct_waterconnections_no_repeat = \
                self.waterconnections_no_repeat(vals['irrigationpointwc_ids'])
            if not correct_waterconnections_no_repeat:
                raise exceptions.UserError(_('There are repeated water '
                                             'connections.'))
            if (check_wcs_diff_sector):
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

    @api.depends('irrigationpoint_ids', 'irrigationpoint_ids.with_pumping')
    def _compute_with_pumping(self):
        for record in self:
            with_pumping = False
            for irrigationpoint in record.irrigationpoint_ids:
                if irrigationpoint.with_pumping:
                    with_pumping = True
                    break
            record.with_pumping = with_pumping


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

    with_pumping = fields.Boolean(
        string='With pumping',
        store=True,
        compute='_compute_with_pumping')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_partner_id',)

    @api.depends('waterconnection_id', 'waterconnection_id.irrigationshed_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            if record.waterconnection_id:
                record.irrigationshed_id =\
                    record.waterconnection_id.irrigationshed_id
            else:
                record.irrigationshed_id = None

    @api.depends('waterconnection_id', 'waterconnection_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            if record.waterconnection_id:
                record.hydraulicsector_id =\
                    record.waterconnection_id.hydraulicsector_id
            else:
                record.hydraulicsector_id = None

    @api.depends('irrigationgate_id', 'irrigationgate_id.irrigationditch_id')
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

    @api.depends('parcel_id', 'parcel_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if (record.parcel_id and record.parcel_id.partner_id):
                partner_id = record.parcel_id.partner_id
            record.partner_id = partner_id

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

    @api.depends('waterconnection_id', 'waterconnection_id.with_pumping')
    def _compute_with_pumping(self):
        for record in self:
            with_pumping = False
            if (record.waterconnection_id and
               record.waterconnection_id.with_pumping):
                with_pumping = True
            record.with_pumping = with_pumping


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

    @api.depends('waterconnection_id', 'waterconnection_id.irrigationshed_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            if record.waterconnection_id:
                record.irrigationshed_id =\
                    record.waterconnection_id.irrigationshed_id
            else:
                record.irrigationshed_id = None

    @api.depends('waterconnection_id', 'waterconnection_id.hydraulicsector_id')
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
