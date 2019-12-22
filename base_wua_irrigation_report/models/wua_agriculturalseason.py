# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    def _default_volume_time_equivalence(self):
        resp = 0
        default_volume_time_equivalence = self.env['ir.values'].get_default(
            'wua.configuration', 'volume_time_equivalence')
        if default_volume_time_equivalence:
            resp = default_volume_time_equivalence
        return resp

    irrigationreport_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.irrigationreport",
        inverse_name="agriculturalseason_id")

    number_of_irrigationreports = fields.Integer(
        string="N. of Irrig. Reports",
        index=True,
        store=True,
        compute="_compute_number_of_irrigationreports")

    num_irrigationreports_stat = fields.Integer(
        string="N. Reports",
        compute="_compute_num_irrigationreports_stat")

    total_volume = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 4),
        store=True,
        compute="_compute_total_volume")

    volume_time_equivalence = fields.Float(
        string='Volume per hour (m3)',
        digits=(32, 4),
        default=_default_volume_time_equivalence,
        required=True,
        help='Volume, in m3, which is equal to one hour')

    @api.depends('irrigationreport_ids')
    def _compute_number_of_irrigationreports(self):
        for record in self:
            number_of_irrigationreports = 0
            if record.irrigationreport_ids:
                number_of_irrigationreports = len(record.irrigationreport_ids)
            record.number_of_irrigationreports = number_of_irrigationreports

    @api.multi
    def _compute_num_irrigationreports_stat(self):
        for record in self:
            record.num_irrigationreports_stat = \
                record.number_of_irrigationreports

    @api.depends('irrigationreport_ids', 'irrigationreport_ids.volume_real')
    def _compute_total_volume(self):
        for record in self:
            total_volume = 0.0
            for irrigationreport in record.irrigationreport_ids:
                total_volume += irrigationreport.volume_real
            record.total_volume = total_volume

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaAgriculturalseason, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            data_in_hours = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'data_in_hours')
            if not data_in_hours:
                for node in doc.xpath(
                   "//field[@name='volume_time_equivalence']"):
                    node.set('invisible', '1')
                    if view_type == 'tree':
                        node.set('modifiers', '{"tree_invisible": true}')
                    else:
                        node.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'volume_time_equivalence' in vals:
            recalculate_volumes = False
            data_in_hours = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'data_in_hours')
            if data_in_hours:
                previous_value = self.volume_time_equivalence
                current_value = vals['volume_time_equivalence']
                if previous_value != current_value:
                    current_agriculturalseason_id = self.id
                    validated_irrigationreports = \
                        self.env['wua.irrigationreport'].search(
                            [('agriculturalseason_id', '=',
                              current_agriculturalseason_id),
                             ('state', '=', 'validated')])
                    if validated_irrigationreports:
                        raise exceptions.UserError(
                            _('There are some validated irrigation reports '
                              'for this agricultural season, and, therefore, '
                              'it is not possible to change the '
                              '\"Volume-per-hour\" field.\n\n'
                              'Before it is necessary to change the state '
                              'to \"draft\".'))
                    else:
                        recalculate_volumes = True
            super(WuaAgriculturalseason, self).write(vals)
            if recalculate_volumes:
                irrigationreports = self.env['wua.irrigationreport'].search(
                    [('agriculturalseason_id', '=',
                      current_agriculturalseason_id)])
                irrigationreports._compute_volume()
        else:
            super(WuaAgriculturalseason, self).write(vals)
        return True

    @api.multi
    def action_see_irrigationreports(self):
        self.ensure_one()
        if self.irrigationreport_ids:
            id_tree_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_form').id
            search_view = self.env.ref(
                'base_wua_irrigation_report.'
                'wua_irrigationreport_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Irrigation Reports'),
                'res_model': 'wua.irrigationreport',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.irrigationreport_ids.ids)]
                }
            return act_window
