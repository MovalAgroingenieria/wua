# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
from lxml import etree
import datetime
import logging
import pytz
from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    mapped_parcel = fields.Boolean(
        string='Mapped Parcel',
        default=False,
    )

    class_sharer = fields.Char(
        string='Class Sharer',
        index=True,
    )

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
                        FROM wua_gis_parcel_class WHERE name =
                        NEW.name LIMIT 1) /
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

    def should_create_parcel_class_on_creation(self, parcel_vals):
        return ('parcel_class_ids' not in parcel_vals or
                len(parcel_vals['parcel_class_ids']) < 1)

    def populate_parcel_class_for_creation(self, parcel_vals):
        parcel_vals['parcel_class_ids'] = [[
            0,
            False,
            {
                'area_official': parcel_vals['area_official'],
                'parcel_class': 'RH',
                'active': parcel_vals['active'] if 'active' in
                parcel_vals else False,
            },
        ]]

    def _get_cayc_connect_query(self):
        cayc_remote_ip = self.env['ir.values'].get_default(
            'wua.configuration', 'cayc_remote_ip')
        cayc_remote_port = self.env['ir.values'].get_default(
            'wua.configuration', 'cayc_remote_port')
        cayc_remote_database = self.env['ir.values'].get_default(
            'wua.configuration', 'cayc_remote_database')
        cayc_remote_database_user = self.env['ir.values'].get_default(
            'wua.configuration', 'cayc_remote_database_user')
        cayc_remote_database_password = self.env['ir.values'].get_default(
            'wua.configuration', 'cayc_remote_database_password')
        if (not cayc_remote_ip or not cayc_remote_port or not
            cayc_remote_database or not cayc_remote_database_user or not
                cayc_remote_database_password):
            raise exceptions.UserError(
                _('Missing some CAYC connect parameter.'))
        cayc_general_connect_query = """
                SELECT dblink_connect('conn_to_cayc', 'hostaddr=%s
                port=%s dbname=%s user=%s password=%s') AS connection;
            """ % (cayc_remote_ip, cayc_remote_port, cayc_remote_database,
                   cayc_remote_database_user, cayc_remote_database_password)
        return cayc_general_connect_query

    def _reset_mapped_parcel_local(self):
        self.env.cr.execute("""
            UPDATE wua_parcel SET mapped_parcel = FALSE
            WHERE active IS TRUE;
        """)

    def _open_cayc_connection(self, connection_query):
        self.env.cr.execute(connection_query)
        connect_result = self.env.cr.dictfetchall()
        if (not connect_result or not
                connect_result[0].get('connection') == 'OK'):
            raise exceptions.ValidationError(
                _('Could not connect to CAYC DB check connection parameters.'))

    def _get_wuabase_id_from_cayc(self, wuabase):
        wuabase_id = None
        self.env.cr.execute("""
            SELECT id FROM dblink('conn_to_cayc', 'SELECT id FROM
            wua_wuabase WHERE name = ''%s'';') AS t(id INTEGER)
        """ % wuabase)
        wuabase_id_results = self.env.cr.dictfetchall()
        if (wuabase_id_results and wuabase_id_results[0].get('id')):
            wuabase_id = wuabase_id_results[0].get('id')
        return wuabase_id

    def _reset_mapped_parcel_remote(self, wuabase_id):
        self.env.cr.execute("""
            SELECT dblink_exec('conn_to_cayc', 'UPDATE wua_parcel
            SET mapped_parcel = FALSE WHERE active AND NOT
            is_primary AND wuabase_id = %s;')
        """ % wuabase_id)

    def _get_parcels_remote(self, wuabase_id):
        parcels = False
        self.env.cr.execute("""
            SELECT STRING_AGG(quote_literal(name), ',') AS parcels FROM
            dblink('conn_to_cayc',
            'SELECT name FROM wua_parcel WHERE active AND NOT
            is_primary AND wuabase_id = %s;') AS t(name TEXT);
        """ % (wuabase_id))
        parcel_results = self.env.cr.dictfetchall()
        if (parcel_results and parcel_results[0].get('parcels')):
            parcels = parcel_results[0].get('parcels')
        return parcels

    def _get_parcels_local(self):
        parcels = False
        self.env.cr.execute("""
            SELECT STRING_AGG('''' || quote_literal(name) || '''', ',') AS
            parcels FROM
            wua_parcel WHERE active;
        """)
        parcel_results = self.env.cr.dictfetchall()
        if (parcel_results and parcel_results[0].get('parcels')):
            parcels = parcel_results[0].get('parcels')
        return parcels

    def _set_mapped_parcel_remote(self, parcels):
        self.env.cr.execute("""
            SELECT dblink_exec('conn_to_cayc',
            'UPDATE wua_parcel SET mapped_parcel = TRUE
            WHERE name IN (%s);');
        """ % parcels)

    def _set_mapped_parcel_local(self, parcels):
        self.env.cr.execute("""
            UPDATE wua_parcel SET mapped_parcel = TRUE WHERE
            name IN (%s);
        """ % parcels)

    def _get_partner_of_mapped_parcels(self):
        partner_ids = False
        self.env.cr.execute("""
            SELECT DISTINCT wpp1.partner_id
            FROM wua_parcel_partnerlink wpp1 INNER JOIN wua_parcel wp1 ON
            wp1.id = wpp1.parcel_id WHERE wp1.active AND wp1.mapped_parcel;
        """)
        partner_results = self.env.cr.fetchall()
        if (partner_results and len(partner_results) > 0):
            partner_ids = [partner[0] for partner in partner_results]
        return partner_ids

    @api.model
    def refresh_mapped_field(self):
        # Check parameters are filled
        _logger = logging.getLogger(self.__class__.__name__)
        connected_to_db = False
        # Refresh Parcel Mapped field
        try:
            # Get connection parameters
            cayc_general_connect_query = self._get_cayc_connect_query()
            self.env.cr.savepoint()
            # Set local parcels as not mapped
            self._reset_mapped_parcel_local()
            self._open_cayc_connection(cayc_general_connect_query)
            connected_to_db = True
            wua_code = self.env['res.company'].search([])[0].wua_code
            wuabase_id = self._get_wuabase_id_from_cayc(wua_code)
            # Set remote parcels as not mapped
            self._reset_mapped_parcel_remote(wuabase_id)
            # Get parcels that need to be updated
            parcels = self._get_parcels_remote(wuabase_id)
            if (parcels):
                # Set local parcels as mapped
                self._set_mapped_parcel_local(parcels)
            # Get parcels that need to be updated on remote
            parcels = self._get_parcels_local()
            if (parcels):
                # Set remote parcels as mapped
                self._set_mapped_parcel_remote(parcels)
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception as e:
            self.env.cr.rollback()
            _logger.error("An error occurred: %s", e)
        finally:
            # Always close db connection if entablished
            if (connected_to_db):
                self.env.cr.execute("""
                SELECT dblink_disconnect('conn_to_cayc');
            """)
        # Refresh Partner Mapped field
        try:
            self.env.cr.savepoint()
            partner_ids = self._get_partner_of_mapped_parcels()
            if (partner_ids):
                self.env['res.partner'].browse(partner_ids).write({
                    'mapped_partner': True,
                })
        except Exception as e:
            self.env.cr.rollback()
            _logger.error("An error occurred: %s", e)

    def do_process_active_field(self, active):
        super(WuaParcel, self).do_process_active_field(active)
        parcel_id = self.id
        parcel_classes = self.env['wua.parcel.class'].with_context(
            active_test=False)
        filtered_parcel_classes = parcel_classes.search(
            [('parcel_id', '=', parcel_id)])
        filtered_parcel_classes.write({
            'active': active
        })


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
        ('RH', 'RH'),
        ('ER', 'ER'),
        ('BR', 'BR'),
        ('NR', 'NR'),
        ('NER', 'NER'),
        ('NBR', 'NBR'),
    ], string='Parcel Class',
        required=True,
        index=True,
        default='RH',
    )

    class_sharer = fields.Char(
        string='Class Sharer',
        related='parcel_id.class_sharer',
        store=True,
        index=True,
    )

    resolution_year = fields.Integer(
        string='Resolution Year',
        index=True,
        default=0,
    )

    notes = fields.Html(
        string='Notes',
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
        ('valid_resolution_year',
         'CHECK (resolution_year >= 0)',
         'The resolution year must be a value zero or positive.'),
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
        if view_type == 'tree' or view_type == 'form':
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

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }
