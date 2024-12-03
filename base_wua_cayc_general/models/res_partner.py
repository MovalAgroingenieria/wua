# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math
import logging
from lxml import etree
from odoo import models, fields, _, exceptions, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    FIELDS_TO_RECOVER_FROM_REMOTE = [
        'name', 'lastname', 'lastname2', 'email', 'phone', 'mobile',
        'street', 'street2', 'city', 'zip', 'state_id', 'country_id', 'title',
        'is_company', 'type', 'website', 'vat', 'lang', 'tz', 'is_wua_partner',
        'comment', 'street_num',
    ]

    is_primary = fields.Boolean(
        string='Is primary Partner',
        compute='_compute_is_primary',
        store=True,
        index=True,
    )

    wuabase_id = fields.Many2one(
        string='Primary Entity',
        comodel_name='wua.wuabase',
        compute='_compute_wuabase_id',
        store=True,
        index=True,
    )

    partner_type = fields.Selection([
        ('01_WUA', 'Water User Association'),
        ('02_IND', 'Industry'),
        ('03_WSP', 'Water Supply'),
        ('04_HEL', 'Hydroelectric Producer'),
    ], string='Partner Type',
        index=True,
    )

    octroi_id = fields.Many2one(
        string='Octroi',
        comodel_name='wua.octroi',
        index=True,
        ondelete='restrict',
    )

    zone_id = fields.Many2one(
        string='Zone',
        comodel_name='wua.zone',
        index=True,
        ondelete='restrict',
    )

    is_independent = fields.Boolean(
        string='Independent Partner',
        default=True,
    )

    parent_partner_id = fields.Many2one(
        string='Parent Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='set null',
        domain="[('is_independent', '=', True),"
               "('is_primary', '=', True),"
               "('partner_type', '=', '01_WUA')]",
    )

    concession_as_volume = fields.Float(
        string='Concession As Volume',
        digits=(32, 4),
        default=0,
    )

    concession_as_power = fields.Float(
        string='Concession As Power',
        digits=(32, 4),
        default=0,
    )

    _sql_constraints = [
        ('valid_concession_as_volume',
         'CHECK (concession_as_volume >= 0)',
         'The concession as volume must be a value zero or positive.'),
        ('valid_concession_as_power',
         'CHECK (concession_as_power >= 0)',
         'The concession as power must be a value zero or positive.'),
    ]

    @api.constrains('partner_code')
    def _check_partner_code(self):
        super(ResPartner, self)._check_partner_code()
        if ((self.env.context.get('wua') == '1' or self.is_wua_partner) and
                (not self.parent_id)):
            # Primary partenr
            if (self.partner_code > 9999 and self.partner_code % 10000 == 0):
                raise exceptions.ValidationError(
                    _('The secondary partner code must not end at 0.'))
            else:
                # Primary partner
                code_to_search = str(self.partner_code).zfill(3)
                if (self.partner_code > 10000):
                    # Secondary partner
                    code_to_search = str(self.partner_code / 10000).zfill(3)
                    wuabase = self.env['wua.wuabase'].search(
                        [('name', '=', code_to_search)])
                    if (not wuabase or len(wuabase) < 1):
                        raise exceptions.ValidationError(
                            _('The Primary Entity code does not exists.'))

    @api.constrains('is_primary', 'partner_type')
    def check_partner_type(self):
        for record in self:
            if (record.is_primary and not record.partner_type):
                raise exceptions.ValidationError(
                    _('A primary partner must have a valid partner type .'))

    @api.depends('partner_code')
    def _compute_is_primary(self):
        for record in self:
            is_primary = False
            if (record.partner_code > 0 and record.partner_code < 10000):
                is_primary = True
            record.is_primary = is_primary

    @api.depends('partner_code')
    def _compute_wuabase_id(self):
        for record in self:
            wuabase_id = None
            code_to_search = False
            if (record.partner_code < 10000):
                code_to_search = str(record.partner_code).zfill(3)
            elif (record.partner_code >= 10000):
                code_to_search = str(record.partner_code / 10000).zfill(3)
            # IDEA: self.env.ref?
            if (code_to_search):
                wuabase_id = self.env['wua.wuabase'].search(
                    [('name', '=', code_to_search)])
            record.wuabase_id = wuabase_id

    # Overwrite method to avoid errors on duplicated NIF
    # It's a possibility that partnes are primary entities and secondary
    # or there are secondary on multiple primary entities
    def exists_vat(self, vat, excluded_id):
        resp = False
        return resp

    @api.depends('parcel_owner_number_votes', 'parcel_owner_area_hec_votes',
                 'is_primary', 'partner_type',
                 'concession_as_volume', 'concession_as_power')
    def _compute_number_of_votes(self):
        if len(self) != 1:
            return
        if not self.is_primary or not self.is_independent:
            self.number_of_votes = 0
        elif self.partner_type != '01_WUA':
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type')
            votes = 0
            divider = 1
            if (self.partner_type in ['02_IND', '03_WSP']):
                concession_value = self.concession_as_volume
                if self.partner_type == '02_IND':
                    divider = 1000
                else:
                    divider = 4000
            else:
                concession_value = self.concession_as_power
                divider = 2.5
            area_for_votes = (concession_value / divider) * 10000
            if polling_system_type == 2 or polling_system_type == 3:
                if polling_system_type == 2:
                    polling_system_interval = self.env['ir.values'].\
                        get_default('wua.configuration',
                                    'polling_system_interval')
                    if polling_system_interval > 0:
                        polling_system_rounding_type = \
                            self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_rounding_type')
                        calc_votes =\
                            area_for_votes / float(polling_system_interval)
                        if polling_system_rounding_type == 0:
                            votes = math.ceil(calc_votes)
                        else:
                            votes = math.floor(calc_votes)
                if polling_system_type == 3:
                    polling_system_intervals = self.env['ir.values'].\
                        get_default('wua.configuration',
                                    'polling_system_intervals')
                    if polling_system_intervals:
                        votes = self.assign_votes_by_range(
                            area_for_votes, polling_system_intervals)
            self.number_of_votes = votes
        else:
            super(ResPartner, self)._compute_number_of_votes()

    def clear_vals_for_che_partner(self, vals):
        vals['customer'] = False
        vals['partner_type'] = None
        vals['concession_as_volume'] = 0.0
        vals['concession_as_power'] = 0.0

    @api.model
    def create(self, vals):
        if ('partner_code' in vals and vals['partner_code'] > 9999):
            self.clear_vals_for_che_partner(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('partner_code' in vals and vals['partner_code'] > 9999):
            self.clear_vals_for_che_partner(vals)
        return super(ResPartner, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        result = super(ResPartner, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            if (self.env.context.get('is_primary_partner', False)):
                hide_fields = [
                    'parcel_owner_number',
                    'parcel_lessee_number',
                    'parcel_lessee_area',
                ]
            else:
                hide_fields = [
                    'partner_type',
                    'octroi_id',
                    'zone_id',
                ]
            for field in hide_fields:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            result['arch'] = etree.tostring(doc)
        return result

    def _get_wuabase_connect_query(self, wuabase):
        server_remote_ip = wuabase.server_remote_ip
        server_remote_port = wuabase.server_remote_port
        server_remote_database = wuabase.server_remote_database
        server_remote_database_user = wuabase.server_remote_database_user
        server_remote_database_password = \
            wuabase.server_remote_database_password
        if (not server_remote_ip or not server_remote_port or not
            server_remote_database or not server_remote_database_user or not
                server_remote_database_password):
            raise exceptions.UserError(
                _('Missing some Server connect parameter.'))
        connect_query = """
                SELECT dblink_connect('conn_to_crbase', 'hostaddr=%s
                port=%s dbname=%s user=%s password=%s') AS connection;
            """ % (server_remote_ip, server_remote_port,
                   server_remote_database, server_remote_database_user,
                   server_remote_database_password)
        return connect_query

    def _open_server_connection(self, connection_query):
        self.env.cr.execute(connection_query)
        connect_result = self.env.cr.dictfetchall()
        if (not connect_result or not
                connect_result[0].get('connection') == 'OK'):
            raise exceptions.ValidationError(
                _('Could not connect to Server DB check connection '
                  'parameters.'))

    def _get_partner_codes_remote(self):
        partner_codes = []
        self.env.cr.execute("""
            SELECT partner_code FROM dblink('conn_to_crbase',
            'SELECT partner_code FROM res_partner WHERE active AND
            mapped_partner') AS
            t(partner_code BIGINT);
        """)
        partner_results = self.env.cr.fetchall()
        if (partner_results and len(partner_results) > 0):
            partner_codes = [partner[0] for partner in partner_results]
        return partner_codes

    def _process_partner_data_from_sql(self, partner_data):
        model_res_better_zip = self.env['res.better.zip']
        if 'is_company' in partner_data:
            partner_data['is_company'] = partner_data['is_company'] == 't'
        if 'zip' in partner_data:
            zip_code = partner_data['zip']
            better_zip = model_res_better_zip.search(
                [('name', '=', zip_code)])
            if better_zip:
                partner_data['state_id'] = better_zip[0].state_id.id
                partner_data['country_id'] = better_zip[0].country_id.id

    def _get_partner_data_from_code_remote(self, partner_code):
        partner_data = False
        self.env.cr.execute("""
            SELECT * FROM dblink('conn_to_crbase',
            'SELECT %s FROM res_partner WHERE active AND
             partner_code = %s') AS
            t(%s);
        """ % (', '.join(self.FIELDS_TO_RECOVER_FROM_REMOTE), partner_code,
               ' TEXT, '.join(self.FIELDS_TO_RECOVER_FROM_REMOTE) + ' TEXT'))
        partner_results = self.env.cr.dictfetchall()
        if (partner_results and len(partner_results) > 0):
            partner_data = partner_results[0]
            self._process_partner_data_from_sql(partner_data)
        return partner_data

    def _process_partnerlink_data_from_sql(self, partnerlink_data, wuabase):
        pl_data = False
        code_of_wuabase = int(wuabase.name)
        wuabase_padder = code_of_wuabase * 10000
        if 'partner_code' in partnerlink_data:
            partner = self.env['res.partner'].search(
                [('partner_code', '=',
                  partnerlink_data['partner_code'] + wuabase_padder)])
            if (partner and len(partner) > 0):
                partnerlink_data['partner_id'] = partner.id
                del partnerlink_data['partner_code']
                pl_data = partnerlink_data
        return pl_data

    def _get_partnerlinks_of_parcel_from_remote(self, parcel, wuabase):
        partnerlinks_data = False
        self.env.cr.execute("""
            SELECT * FROM dblink('conn_to_crbase',
            'SELECT rp1.partner_code, wpp1.irrigation_partner, wpp1.profile,
            wpp1.is_usufructuary, wpp1.ownership_percentage,
            wpp1.water_costs_percentage, wpp1.other_costs_percentage FROM
            wua_parcel_partnerlink wpp1 INNER
            JOIN res_partner rp1 ON wpp1.partner_id = rp1.id INNER JOIN
            wua_parcel wp1 ON wpp1.parcel_id = wp1.id WHERE
            rp1.active AND wp1.active AND wp1.name = ''%s'' ;') AS
            t(partner_code BIGINT, irrigation_partner BOOLEAN, profile TEXT,
            is_usufructuary BOOLEAN, ownership_percentage NUMERIC,
            water_costs_percentage NUMERIC, other_costs_percentage NUMERIC);
        """ % parcel.name)
        pl_results = self.env.cr.dictfetchall()
        if (pl_results and len(pl_results) > 0):
            partnerlinks_data = []
            for pl in pl_results:
                pl_data = self._process_partnerlink_data_from_sql(pl, wuabase)
                if (pl_data):
                    partnerlinks_data.append((0, 0, pl_data))
        return partnerlinks_data

    def _update_partner_status_from_remote(self, partner, partner_code):
        if (not partner.active):
            partner.active = True
        partner_data = self._get_partner_data_from_code_remote(
            partner_code)
        if (partner_data):
            partner.write(partner_data)

    def _create_partner_from_remote(self, partner_code, partner_code_che):
        model_res_partner = self.env['res.partner'].with_context(
            {'wua': '1', 'default_is_wua_partner': True, 'active_test': False})
        partner_data = self._get_partner_data_from_code_remote(partner_code)
        if (partner_data):
            partner_data['partner_code'] = partner_code_che
            model_res_partner.create(partner_data)

    def refresh_partners_of_wuabase(self, wuabase):
        _logger = logging.getLogger(self.__class__.__name__)
        code_of_wuabase = int(wuabase.name)
        # Padder for partner code of che partners
        wuabase_padder = code_of_wuabase * 10000
        connected_to_db = False
        try:
            connect_query = self._get_wuabase_connect_query(wuabase)
            self._open_server_connection(connect_query)
            connected_to_db = True
            partner_codes = self._get_partner_codes_remote()
            # Get partners of wuabase that are no longer on that wuabase
            # And archive them
            partners_not_in_base = self.env['res.partner'].search(
                [('partner_code', '>', wuabase_padder),
                 ('partner_code', '<', wuabase_padder + 10000),
                 ('partner_code', 'not in', partner_codes)])
            for partner in partners_not_in_base:
                partner.active = False
            # Get partners from remote and create or edit (Unarchive if
            # necessary)
            for pc in partner_codes:
                partner_code_che = pc + wuabase_padder
                partner = self.env['res.partner'].with_context(
                    active_test=False).search(
                    [('partner_code', '=', partner_code_che)])
                if (partner and len(partner) > 0):
                    self._update_partner_status_from_remote(partner, pc)
                else:
                    self._create_partner_from_remote(pc, partner_code_che)
            # Update partnerlinks of mapped parcels
            parcels_to_update = wuabase.parcel_mapped_ids
            for parcel in parcels_to_update:
                partnerlinks_of_parcel = self.\
                    _get_partnerlinks_of_parcel_from_remote(parcel, wuabase)
                # Empty and add the new partnerlink data
                # (5, 0, 0) not working because write on base_wua
                parcel.partnerlink_ids.unlink()
                if (partnerlinks_of_parcel):
                    # Empty and then add
                    # partnerlinks_of_parcel.insert(0, (5, 0, 0))
                    parcel.write({
                        'partnerlink_ids': partnerlinks_of_parcel,
                    })
            wuabase.last_syncrhonization_date = fields.Datetime.now()
        except Exception as e:
            self.env.cr.rollback()
            _logger.error("An error occurred: %s", e)
            wuabase.message_post(
                body="Error %s: " % e
            )
        finally:
            # Always close db connection if entablished
            if (connected_to_db):
                self.env.cr.execute("""
                SELECT dblink_disconnect('conn_to_crbase');
            """)

    @api.model
    def refresh_partners(self):
        # Check parameters are filled
        wuabases = self.env['wua.wuabase'].search(
            [('server_connected', '=', True)],
            order="last_syncrhonization_date asc")
        for wb in wuabases:
            self.refresh_partners_of_wuabase(wb)
            # For no retrying incorrect wuabases and correct ones get
            # to syncrhonize
            self.env.cr.commit()

    @api.multi
    def action_see_secondary_parcels(self):
        self.ensure_one()
        condition = [
            ('is_primary', '=', False),
            ('wuabase_id', '=', self.wuabase_id.id),
        ]
        id_form_view = self.env.ref(
            'base_wua_cayc_general.wua_parcel_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_cayc_general.wua_parcel_view_tree').id
        search_view = self.env.ref(
            'base_wua_cayc_general.wua_parcel_view_search')
        parcel_label = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
                'base_wua_cayc_general',
                'Parcels',
        )
        if not parcel_label:
            parcel_label = _('Parcels')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': parcel_label,
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'from_shortcut': 1},
        }
        return act_window
