# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
import datetime
from Crypto.Cipher import AES
import pytz


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def get_wua_parcel_comparative_presconsumption_action(self):
        current_parcel_id = self.env.context.get('active_id')
        condition = [('parcel_id', '=', current_parcel_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_parcel_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_parcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.comparative.parcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window


class WuaParcelSubparcel(models.Model):
    _inherit = 'wua.parcel.subparcel'

    tree_development = fields.Selection([
        ('seedlings', 'Seedlings'),
        ('intermediate', 'Intermediate'),
        ('full_production', 'Full production')],
        string='Tree Development'
    )

    shaded_percentage = fields.Float(
        string='Shaded %',
        digits=(32, 2)
    )

    soil_type = fields.Selection([
        ('loamy', 'Loamy'),
        ('clayey', 'Clayey'),
        ('silty', 'Silty'),
        ('sandy', 'Sandy'),
        ('loam_clayey', 'Loam-Clayey'),
        ('loam_silty', 'Loam-Silty'),
        ('loam_sandy', 'Loam-Sandy'),
        ],
        string='Soil Type',
    )

    organic_material_percentage = fields.Float(
        string='Organic Material %',
        digits=(32, 2)
    )

    orientation = fields.Integer(
        string='Orientation',
        help='Value between 0 and 359º (0 corresponds to geographic north)'
    )

    drippers_number = fields.Integer(
        string='Number of drippers',
    )

    drippers_nominal_flow = fields.Float(
        string='Drip. Nom. Flow (l/h)',
        digits=(32, 2)
    )

    tree_lateral_number = fields.Integer(
        string='N. of lateral/tree'
    )

    plantation_year = fields.Integer(
        string='Plantation Year',
    )

    cultivation_age = fields.Integer(
        string='Cultivation Age',
        compute='_compute_cultivation_age',
        search='_search_cultivation_age'
    )

    tree_distance = fields.Float(
        string='M. between trees',
        digits=(32, 2)
    )

    row_distance = fields.Float(
        string='M. between rows',
        digits=(32, 2)
    )

    tree_drippers_number = fields.Integer(
        string='N. of drippers/tree',
    )

    notes = fields.Html(
        string='Notes'
    )

    aerial_img = fields.Binary(
        string="Aerial Image",
        readonly=True,
        attachment=True,
        compute='_compute_aerial_img'
    )

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        compute='_compute_cadastral_reference',
        store=True
    )

    cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_cadastral_reference_link',
        store=True
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link'
    )

    updated_in_remotecontrol = fields.Boolean(
        string='Updated in Remote Control',
        compute='_compute_updated_in_telecontrol'
    )

    subparcel_modified = fields.Boolean(
        string='Modified',
        default=False,
    )

    subparcel_presconsumption_ids = fields.One2many(
        string="Comparative Subparcel Presconsumption",
        comodel_name="wua.comparative.subparcel.presconsumption",
        inverse_name="subparcel_id"
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4),
        compute='_compute_estimated_consumption',
        store=True
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4),
        compute='_compute_real_consumption',
        store=True
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True
    )

    _sql_constraints = [
        ('valid_shaded_percentage',
         'CHECK (shaded_percentage >= 0 and shaded_percentage <= 100)',
         'The shaded percentage must be a value from 0 to 100.'),
        ('valid_organic_material_percentage',
         'CHECK (organic_material_percentage >= 0 and '
         'organic_material_percentage <= 100)',
         'The organic material percentage must be a value from 0 to 100.'),
        ('valid_orientation',
         'CHECK (orientation >= 0 and orientation <= 360)',
         'The orientation must be a value between 0 and 360 degrees.'),
        ('valid_drippers_number',
         'CHECK (drippers_number >= 0)',
         'The number of drippers cannot be a negative value.'),
        ('valid_drippers_nominal_flow',
         'CHECK (drippers_nominal_flow >= 0)',
         'The drippers nominal-flow cannot be a negative value.'),
        ('valid_plantation_year',
         'CHECK (plantation_year >= 0)',
         'The plantation year cannot be a negative value.'),
        ('valid_tree_lateral_number',
         'CHECK (tree_lateral_number >= 0 and tree_lateral_number <= 2)',
         'The \"N. of lateral/tree\" value must be 1 or 2.'),
        ('valid_tree_distance',
         'CHECK (tree_distance >= 0)',
         'The distance between trees cannot be a negative value.'),
        ('valid_row_distance',
         'CHECK (row_distance >= 0)',
         'The distance between rows cannot be a negative value.'),
        ('valid_tree_drippers_number',
         'CHECK (tree_drippers_number >= 0 and tree_drippers_number <= 2)',
         'The \"N. of drippers/tree\" value must be 1 or 2.'),
        ]

    @api.multi
    def _compute_cultivation_age(self):
        for record in self:
            cultivation_age = 0
            if record.plantation_year:
                current_year = int(datetime.date.today().strftime("%Y"))
                cultivation_age = current_year - record.plantation_year
            record.cultivation_age = cultivation_age

    @api.multi
    def _compute_aerial_img(self):
        for record in self:
            aerial_img = None
            if record.parcel_id.aerial_img:
                aerial_img = record.parcel_id.aerial_img
            record.aerial_img = aerial_img

    @api.depends('parcel_id', 'parcel_id.cadastral_reference_link')
    def _compute_cadastral_reference_link(self):
        for record in self:
            cadastral_reference_link = None
            if record.parcel_id.cadastral_reference_link:
                cadastral_reference_link = \
                    record.parcel_id.cadastral_reference_link
            record.cadastral_reference_link = cadastral_reference_link

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.estimated_consumption')
    def _compute_estimated_consumption(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
        for record in self:
            estimated_consum = 0
            if (record.subparcel_presconsumption_ids and
               active_agriculturalseason):
                filtered_subparcel_presconsumption_ids = filter(
                    lambda x: x['agriculturalseason_id'] ==
                    active_agriculturalseason,
                    record.subparcel_presconsumption_ids)
                if filtered_subparcel_presconsumption_ids:
                    for sub_presc in filtered_subparcel_presconsumption_ids:
                        estimated_consum += sub_presc.estimated_consumption
            record.estimated_consumption = estimated_consum

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.real_consumption')
    def _compute_real_consumption(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
        for record in self:
            real_consumption = 0
            if (record.subparcel_presconsumption_ids and
               active_agriculturalseason):
                filtered_subparcel_presconsumption_ids = filter(
                    lambda x: x['agriculturalseason_id'] ==
                    active_agriculturalseason,
                    record.subparcel_presconsumption_ids)
                if filtered_subparcel_presconsumption_ids:
                    for sub_presc in filtered_subparcel_presconsumption_ids:
                        real_consumption += sub_presc.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.multi
    def action_regenerate_comparative_consumptions(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
            cp_model = self.env['wua.controlperiod']
            controlperiods = cp_model.search(
                [('agriculturalseason_id', '=', active_agriculturalseason.id)])
            for controlperiod in (controlperiods or []):
                cp_model.regenerate_comparative_consumptions_of_controlperiod(
                    controlperiod)

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
        for record in self:
            url_for_record = url
            if url_for_record:
                if parcel_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + str(record.parcel_id.name)
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
                aes_encryptor = AES.new('hZj<?*aS9w.Rg)3"', AES.MODE_CBC, iv)
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

    @api.depends('parcel_id', 'parcel_id.cadastral_reference')
    def _compute_cadastral_reference(self):
        for record in self:
            cadastral_reference = None
            if record.parcel_id.cadastral_reference:
                cadastral_reference = record.parcel_id.cadastral_reference
            record.cadastral_reference = cadastral_reference

    @api.depends('parcel_id', 'parcel_id.updated_in_remotecontrol')
    def _compute_updated_in_telecontrol(self):
        for record in self:
            updated_in_remotecontrol = None
            if record.parcel_id.updated_in_remotecontrol:
                updated_in_remotecontrol = \
                    record.parcel_id.updated_in_remotecontrol
            record.updated_in_remotecontrol = updated_in_remotecontrol

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_see_cadastral_report(self):
        self.ensure_one()
        if self.cadastral_reference_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.cadastral_reference_link,
                'target': 'new',
            }

    @api.model
    def create(self, vals):
        new_subparcel = super(WuaParcelSubparcel, self).create(vals)
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if (len(active_agriculturalseason) == 1):
            comp_subp_presc = \
                self.env['wua.comparative.subparcel.presconsumption']
            for controlperiod in active_agriculturalseason.controlperiod_ids:
                comp_subp_presc.create({
                    'subparcel_id': new_subparcel.id,
                    'parcel_id': new_subparcel.parcel_id.id,
                    'cadastral_reference':
                        new_subparcel.parcel_id.cadastral_reference,
                    'area_perc': new_subparcel.area_perc,
                    'irrigationsystem_id':
                        new_subparcel.irrigationsystem_id.id,
                    'tree_distance': new_subparcel.tree_distance,
                    'tree_drippers_number': new_subparcel.tree_drippers_number,
                    'tree_development': new_subparcel.tree_development,
                    'tree_lateral_number': new_subparcel.tree_lateral_number,
                    'row_distance': new_subparcel.row_distance,
                    'controlperiod_id': controlperiod.id,
                    'partner_id': new_subparcel.partner_id.id,
                    'hydraulicsector_id': new_subparcel.hydraulicsector_id.id,
                    'cultivation_id': new_subparcel.cultivation_id.id,
                    'cultivationvariety_id':
                        new_subparcel.cultivationvariety_id.id,
                    'area_official': new_subparcel.area_official,
                    'productionmethod_id':
                        new_subparcel.productionmethod_id.id,
                    'shaded_percentage': new_subparcel.shaded_percentage,
                    'soil_type': new_subparcel.soil_type,
                    'organic_material_percentage':
                        new_subparcel.organic_material_percentage,
                    'orientation': new_subparcel.orientation,
                    'drippers_number': new_subparcel.drippers_number,
                    'drippers_nominal_flow':
                        new_subparcel.drippers_nominal_flow
                    })
        return new_subparcel

    @api.multi
    def write(self, vals):
        # TODO: Add/remove fields for set "subparcel_modified" field.
        subparcel_modified = ('area_official' in vals or
                              'tree_development' in vals or
                              'shaded_percentage' in vals or
                              'soil_type' in vals or
                              'organic_material_percentage' in vals or
                              'orientation' in vals or
                              'drippers_number' in vals or
                              'drippers_nominal_flow' in vals or
                              'tree_lateral_number' in vals or
                              'plantation_year' in vals or
                              'tree_distance' in vals or
                              'row_distance' in vals or
                              'tree_drippers_number' in vals)
        if subparcel_modified:
            vals['subparcel_modified'] = True
        resp = super(WuaParcelSubparcel, self).write(vals)
        update_vals = {}
        if 'partner_id' in vals:
            update_vals['partner_id'] = vals['partner_id']
        if 'parcel_id' in vals:
            update_vals['parcel_id'] = vals['parcel_id']
            update_vals['cadastral_reference'] = self.env['wua.parcel'].\
                browse(vals['parcel_id']).cadastral_reference
        if 'hydraulicsector_id' in vals:
            update_vals['hydraulicsector_id'] = vals['hydraulicsector_id']
        if 'area_official' in vals:
            update_vals['area_official'] = vals['area_official']
        if 'cultivation_id' in vals:
            update_vals['cultivation_id'] = vals['cultivation_id']
        if 'cultivationvariety_id' in vals:
            update_vals['cultivationvariety_id'] = \
                vals['cultivationvariety_id']
        if 'productionmethod_id' in vals:
            update_vals['productionmethod_id'] = vals['productionmethod_id']
        if 'shaded_percentage' in vals:
            update_vals['shaded_percentage'] = vals['shaded_percentage']
        if 'soil_type' in vals:
            update_vals['soil_type'] = vals['soil_type']
        if 'organic_material_percentage' in vals:
            update_vals['organic_material_percentage'] = \
                vals['organic_material_percentage']
        if 'orientation' in vals:
            update_vals['orientation'] = vals['orientation']
        if 'drippers_number' in vals:
            update_vals['drippers_number'] = vals['drippers_number']
        if 'drippers_nominal_flow' in vals:
            update_vals['drippers_nominal_flow'] = \
                vals['drippers_nominal_flow']
        if 'irrigationsystem_id' in vals:
            update_vals['irrigationsystem_id'] = vals['irrigationsystem_id']
        if 'tree_distance' in vals:
            update_vals['tree_distance'] = vals['tree_distance']
        if 'tree_drippers_number' in vals:
            update_vals['tree_drippers_number'] = vals['tree_drippers_number']
        if 'tree_development' in vals:
            update_vals['tree_development'] = vals['tree_development']
        if 'tree_lateral_number' in vals:
            update_vals['tree_lateral_number'] = vals['tree_lateral_number']
        if 'row_distance' in vals:
            update_vals['row_distance'] = vals['row_distance']
        if 'area_perc' in vals:
            update_vals['area_perc'] = vals['area_perc']
        if (update_vals):
            if (self.subparcel_presconsumption_ids and
                    len(self.subparcel_presconsumption_ids) > 0):
                presconsumptions = self.subparcel_presconsumption_ids.filtered(
                    lambda x: x.controlperiod_id.agriculturalseason_id.
                    active_agriculturalseason)
                if (len(presconsumptions) > 0):
                    for presconsumption in presconsumptions:
                        presconsumption.write(update_vals)
        return resp

    def regenerate_comparative_consumptions(self):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if (len(active_agriculturalseason) == 1):
            for record in self:
                cmp_subp_presc = \
                    self.env['wua.comparative.subparcel.presconsumption']
                cmp_pres_of_subparcel = cmp_subp_presc.search(
                    ['&', ('agriculturalseason_id', '=',
                           active_agriculturalseason.id),
                     ('subparcel_id', '=', record.id)])
                if cmp_pres_of_subparcel:
                    cmp_pres_of_subparcel.unlink()
                for controlperiod in active_agriculturalseason.\
                        controlperiod_ids:
                    cmp_subp_presc.create({
                        'subparcel_id': record.id,
                        'parcel_id': record.parcel_id.id,
                        'cadastral_reference':
                            record.parcel_id.cadastral_reference,
                        'area_perc': record.area_perc,
                        'irrigationsystem_id':
                            record.irrigationsystem_id.id,
                        'tree_distance': record.tree_distance,
                        'tree_drippers_number': record.tree_drippers_number,
                        'tree_development': record.tree_development,
                        'tree_lateral_number': record.tree_lateral_number,
                        'row_distance': record.row_distance,
                        'controlperiod_id': controlperiod.id,
                        'partner_id': record.partner_id.id,
                        'hydraulicsector_id': record.hydraulicsector_id.id,
                        'cultivation_id': record.cultivation_id.id,
                        'cultivationvariety_id':
                            record.cultivationvariety_id.id,
                        'area_official': record.area_official,
                        'productionmethod_id':
                            record.productionmethod_id.id,
                        'shaded_percentage': record.shaded_percentage,
                        'soil_type': record.soil_type,
                        'organic_material_percentage':
                            record.organic_material_percentage,
                        'orientation': record.orientation,
                        'drippers_number': record.drippers_number,
                        'drippers_nominal_flow': record.drippers_nominal_flow,
                        })
                record.subparcel_modified = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _search_cultivation_age(self, operator, value):
        current_year = int(datetime.date.today().strftime("%Y"))
        new_operator = operator
        if operator == '>':
            new_operator = '<'
        elif operator == '>=':
            new_operator = '<='
        elif operator == '<':
            new_operator = '>'
        elif operator == '<=':
            new_operator = '>='
        subparcels = self.env['wua.parcel.subparcel'].search(
            [('plantation_year', '!=', 0),
             ('plantation_year', new_operator, current_year - value)])
        return ([('id', 'in', [x.id for x in subparcels])])

    def get_wua_subparcel_comparative_presconsumption_action(self):
        current_subparcel_id = self.env.context.get('active_id')
        condition = [('subparcel_id', '=', current_subparcel_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_tree').id
        id_form_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_form').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Subparcels'),
            'res_model': 'wua.comparative.subparcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window
