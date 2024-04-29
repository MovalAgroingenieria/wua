# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
from lxml import etree
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    parcel_class_ids = fields.One2many(
        string='Parcel Classes',
        comodel_name='wua.parcel.class',
        inverse_name='parcel_id',
    )

    def check_gis_parcel_class_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_parcel_class')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def create_parcel_class_triggers(self):
        gis_parcel_class_table_created = self.check_gis_parcel_class_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_parcel_class_table_created and
                extension_schema_postgis_created):
            # Function that will update the wua_parcel_class data when the
            # wua_gis_parcel_class table has some change,
            # (Create, Update or Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_parcel_class_update_on_wua_parcel() RETURNS
                    trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_parcel_class SET
                        with_gis_parcel_class = False,
                        area_gis = 0
                    WHERE
                        OLD.name = name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_parcel_class SET with_gis_parcel_class =
                        True WHERE
                        NEW.name = name;
                    UPDATE public.wua_parcel_class SET area_gis =
                        (postgis.ST_Area(NEW.geom) * 0.0001) / (
                    CASE
                        WHEN (SELECT substring(value from '[0-9]+')::INTEGER AS
                            value FROM ir_values WHERE name LIKE
                            'area_measurement_type' LIMIT 1) = 1
                        THEN
                            (SELECT substring(
                                value from'[0-9]+\\.[0-9]+')::FLOAT
                            AS value FROM ir_values WHERE name LIKE
                            'area_measurement_equivalence' LIMIT 1)
                        ELSE 1
                    END
                    )
                    WHERE NEW.name = name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis parcel is unlinked and
            # other when a gis parcel is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_parcel_class_write_trigger ON
                    public.wua_gis_parcel_class;
                DROP TRIGGER IF EXISTS
                    wua_gis_parcel_class_create_unlink_trigger ON
                    public.wua_gis_parcel_class;

                CREATE TRIGGER wua_gis_parcel_class_write_trigger
                AFTER UPDATE OF geom, name ON
                public.wua_gis_parcel_class FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE wua_gis_parcel_class_update_on_wua_parcel();

                CREATE TRIGGER wua_gis_parcel_class_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_parcel_class FOR EACH ROW
                EXECUTE PROCEDURE wua_gis_parcel_class_update_on_wua_parcel();
            """)
            self.env.cr.commit()
            # Function that will update the wua_parcel_class data when the
            # wua_parcel_class table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_parcel_class_update_on_wua_parcel_class()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_parcel_class SET
                    with_gis_parcel_class = (SELECT NEW.name IN
                        (SELECT name FROM wua_gis_parcel_class)),
                    area_gis = (SELECT postgis.ST_Area(geom) * 0.0001
                        FROM wua_gis_parcel_class WHERE name = NEW.name LIMIT 1) /
                        (
                            CASE
                                WHEN (SELECT substring(
                                        value from '[0-9]+')::INTEGER AS value
                                        FROM ir_values WHERE name LIKE
                                        'area_measurement_type' LIMIT 1) = 1
                                THEN (SELECT substring(
                                        value from '[0-9]+\\.[0-9]+')::FLOAT AS
                                        value FROM ir_values WHERE name LIKE
                                        'area_measurement_equivalence' LIMIT 1)
                                ELSE 1
                            END
                        )
                    WHERE name = NEW.name;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the parcel is created and
            # other when a gis parcel is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_parcel_class_write_trigger ON
                    public.wua_parcel_class;
                DROP TRIGGER IF EXISTS wua_parcel_class_create_trigger ON
                    public.wua_parcel_class;

                CREATE TRIGGER wua_parcel_class_write_trigger
                AFTER UPDATE OF name ON
                public.wua_parcel_class FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE
                    wua_parcel_class_update_on_wua_parcel_class();

                CREATE TRIGGER wua_parcel_class_create_trigger
                AFTER INSERT ON
                public.wua_parcel_class FOR EACH ROW
                EXECUTE PROCEDURE
                    wua_parcel_class_update_on_wua_parcel_class();
            """)
            self.env.cr.commit()

    def set_gis_fields_parcel_class(self):
        gis_parcel_classes_ok = self.check_gis_parcel_class_created()
        if (gis_parcel_classes_ok):
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
                    UPDATE public.wua_parcel_class
                    SET area_gis = 0, with_gis_parcel_class = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_parcel_class wpc1
                    SET with_gis_parcel_class = TRUE, area_gis =
                        (postgis.ST_Area(wpc1.geom) * 0.0001) / %s
                    FROM public.wua_gis_parcel_class wgpc1
                    WHERE wpc1.name = wgpc1.name;
                """, [area_measurement_equivalence])
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_parcel_classes_ok = False
        return gis_parcel_classes_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # Parcel Class GIS
        gis_parcel_class_ok = self.set_gis_fields_parcel_class()
        return gis_parcels_ok and gis_parcel_class_ok

    @api.model
    def create(self, vals):
        if 'parcel_class_ids' in vals:
            self.populate_area_official_of_parcel_class(
                vals['parcel_class_ids'], vals['area_official'])
        new_parcel = super(WuaParcel, self).create(vals)
        if len(new_parcel.parcel_class_ids) == 0:
            self.create_parcel_class_unique(new_parcel)
        else:
            correct_parcel_classes_area = self.is_parcel_classes_area_correct(
                new_parcel.id, vals['area_official'],
                vals['parcel_class_ids'])
            if not correct_parcel_classes_area:
                raise exceptions.UserError(_('The sum of classes areas must '
                                             'be the parcel official area.'))

    def do_process_slave_data_for_write(self, vals):
        super(WuaParcel, self).do_process_slave_data_for_write(vals)
        area_official = -1
        parcel_class_ids = None
        if 'area_official' in vals:
            area_official = vals['area_official']
        if 'parcel_class_ids' in vals:
            parcel_class_ids = vals['parcel_class_ids']
        correct_subparcels_area = self.is_parcel_classes_area_correct(
            self.id, area_official, parcel_class_ids)
        if not correct_subparcels_area:
            raise exceptions.UserError(_('The sum of parcel class areas '
                                         'must be the parcel official '
                                         'area.'))

    def do_process_active_field(self, active):
        super(WuaParcel, self).do_process_active_field()
        parcel_id = self.id
        parcel_classes = self.env['wua.parcel.class'].with_context(
            active_test=False)
        filtered_parcel_classes = parcel_classes.search(
            [('parcel_id', '=', parcel_id)])
        filtered_parcel_classes.write({
            'active': active
        })

    def populate_area_official_of_parcel_class(
            self, parcel_class_ids, area_official):
        # if the record is the first class of the parcel
        # and her area is 0, then populate the area.
        if len(parcel_class_ids) == 1 and parcel_class_ids[0][0] == 0:
            vals = parcel_class_ids[0][2]
            if vals['area_official'] == 0:
                vals.update({'area_official': area_official})

    def create_parcel_class_unique(self, parcel):
        parcel_class_model = self.env['wua.parcel.class']
        vals = {
            'parcel_id': parcel.id,
            'area_official': parcel.area_official,
            'parcel_class': 'SAR',
            'active': parcel.active}
        parcel_class_model.create(vals)

    # If the area_official parameter is -1, then find parcel
    # from parcel_id and get her area. If the parcel_class_ids parameter
    # is None, then find all parcel_classes from parcel_id and sum their area.
    def is_parcel_classes_area_correct(
            self, parcel_id, area_official, parcel_class_ids):
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
                if parcel_class_oper == 4 or (parcel_class_oper == 1 and
                   'area_official' not in parcel_class_vals):
                    unchanged_ids.append(parcel_class_id)
                # append parcel_class or update parcel_class with modified area
                if parcel_class_oper == 0 or (parcel_class_oper == 1 and
                   'area_official' in parcel_class_vals):
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


class WuaParcelClass(models.Model):
    _name = 'wua.parcel.class'

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade',
    )

    parcel_class = fields.Selection([
        ('SAR', 'SAR'),
        ('ER', 'ER'),
        ('BR', 'BR'),
        ('NR', 'NR'),
        ('NER', 'NER'),
        ('NBR', 'NBR'),
    ], string='Parcel Class',
        required=True,
        index=True,
        default='sar',
    )

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to '
        'hide the register without removing it. For see archived register, '
        'go to "Search-Filters" in tree view',
    )

    area_official = fields.Float(
        string='Class Official Area',
        digits=(32, 4),
        default=0,
    )

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        readonly=True,
        default=0,
    )

    name = fields.Char(
        string='Parcel Class',
        store=True,
        compute='_compute_name',
        index=True,
    )

    with_gis_parcel_class = fields.Boolean(
        string='GIS Parcel Class',
        store=True,
        compute='_compute_with_gis_parcel_class',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    _sql_constraints = [
        ('valid_area_official',
         'CHECK (area_official >= 0)',
         'The area official must be a value zero or positive.'),
        ('valid_area_gis',
         'CHECK (area_gis >= 0)',
         'The area gis must be a value zero or positive.'),
    ]

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            # Dont create table, import script will do it
            parcel_model.create_parcel_class_triggers()
        except Exception:
            pass

    @api.depends('area_gis')
    def _compute_with_gis_parcel_class(self):
        for record in self:
            with_gis_parcel_class = False
            if record.area_gis > 0:
                with_gis_parcel_class = True
            record.with_gis_parcel_class = with_gis_parcel_class

    @api.depends('parcel_id', 'parcel_id.name', 'parcel_class')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.parcel_id and record.parcel_class:
                name = str(record.parcel_id.name) + '-' + \
                    record.parcel_class
            record.name = name

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_class_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_class_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if parcel_class_param:
                    sep_char = u'?'
                    if url_for_record.find('?') != -1:
                        sep_char = u'&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_class_param + u'=' + record.name
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcelClass, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode(
                    'utf_8')
            if area_measurement_name != '':
                area_measurement_name = ' (' + \
                    area_measurement_name.lower() + ')'
                # Area official
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.env['wua.parcel'].sudo().\
                        get_value_from_translation(
                            'base_wua_cayc',
                            self.__class__.area_official.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
                # Area GIS
                for node in doc.xpath("//field[@name='area_gis']"):
                    original_label = \
                        self.env['wua.parcel'].sudo().\
                        get_value_from_translation(
                            'base_wua_cayc',
                            self.__class__.area_gis.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
            else:
                # Area official
                for node in doc.xpath("//field[@name='area_official']"):
                    node.set(
                        'string', self.env['wua.parcel'].sudo().
                        get_value_from_translation(
                            'base_wua_cayc',
                            self.__class__.area_official.string) +
                        ' (' + _('hectares') + ')')
                # Area GIS
                for node in doc.xpath("//field[@name='area_gis']"):
                    node.set(
                        'string', self.env['wua.parcel'].sudo().
                        get_value_from_translation(
                            'base_wua_cayc',
                            self.__class__.area_gis.string) +
                        ' (' + _('hectares') + ')')
            res['arch'] = etree.tostring(doc)
        return res
