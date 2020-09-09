# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
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
            'context': {'search_default_controlperiod': True,
                        'search_default_agriculturalseasonactive': True},
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
        string='Shaded Percentage',
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
        string='Organica Material Percentage',
        digits=(32, 2)
    )

    orientation = fields.Integer(
        string='Orientation',
        help='Value between 0 and 359º (0 corresponds to geographic north)'
    )

    drippers_number = fields.Integer(
        string='Number of Drippers',
    )

    drippers_nomial_flow = fields.Float(
        string='Drippers Nomial Flow (l/h)',
        digits=(32, 2)
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
        string='Distance between trees (m)',
        digits=(32, 2)
    )

    row_distance = fields.Float(
        string='Distance between rows (m)',
        digits=(32, 2)
    )

    tree_drippers_number = fields.Integer(
        string='Number of drippers by tree',
    )

    tree_lateral_number = fields.Integer(
        string='Number of tree laterals '
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
        compute='_compute_subparcel_modified',
        default=False,
        store=True
    )

    subparcel_presconsumption_ids = fields.One2many(
        string="Comparative Subparcel Presconsumption",
        comodel_name="wua.comparative.subparcel.presconsumption",
        inverse_name="subparcel_id"
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4)
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
                 'subparcel_presconsumption_ids.real_consumption')
    def _compute_real_consumption(self):
        for record in self:
            real_consumption = 0
            if record.subparcel_presconsumption_ids:
                for sub_presc in record.subparcel_presconsumption_ids:
                    real_consumption += sub_presc.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

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

    # TODO: Check which fields can change estimated_consumption
    @api.depends('area_official', 'tree_development', 'shaded_percentage',
                 'soil_type', 'organic_material_percentage', 'orientation')
    def _compute_subparcel_modified(self):
        for record in self:
            subparcel_modified = True
            record.subparcel_modified = subparcel_modified

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
                    'drippers_nomial_flow': new_subparcel.drippers_nomial_flow
                    })
        return new_subparcel

    @api.multi
    def write(self, vals):
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
        if 'drippers_nomial_flow' in vals:
            update_vals['drippers_nomial_flow'] = vals['drippers_nomial_flow']
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
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_controlperiod': True,
                        'search_default_agriculturalseasonactive': True},
            }
        return act_window
