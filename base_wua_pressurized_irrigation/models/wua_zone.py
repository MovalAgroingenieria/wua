from odoo import models, fields, api, _


class WuaZone(models.Model):
    _inherit = 'wua.zone'

    parcel_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='zone_id',
        string='Parcels',
    )
    irrigationshed_ids = fields.One2many(
        comodel_name='wua.irrigationshed',
        inverse_name='zone_id',
        string='Irrigationsheds',
    )
    waterconnection_ids = fields.One2many(
        comodel_name='wua.waterconnection',
        inverse_name='zone_id',
        string='Waterconnections',
    )
    watermeter_ids = fields.One2many(
        comodel_name='wua.watermeter',
        inverse_name='zone_id',
        string='Watermeter',
    )

    @api.multi
    def action_get_waterconnections(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_form').id
        search_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_waterconnection_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterconnections'),
            'res_model': 'wua.waterconnection',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.waterconnection_ids.ids)],
            'context': {'default_zone_id': self.id}
            }
        return act_window

    @api.multi
    def action_get_irrigationsheds(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_irrigationshed_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_irrigationshed_view_form').id
        search_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_irrigationshed_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Irrigationsheds'),
            'res_model': 'wua.irrigationshed',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.irrigationshed_ids.ids)],
            'context': {'default_zone_id': self.id}
            }
        return act_window

    @api.multi
    def action_get_parcels(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_parcel_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_parcel_view_form').id
        search_view = self.env.ref(
            'base_wua_infrastructure.'
            'wua_parcel_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.parcel_ids.ids)],
            'context': {'default_zone_id': self.id}
            }
        return act_window

    @api.multi
    def action_get_watermeters(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_watermeter_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_watermeter_view_form').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_watermeter_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Watermeters'),
            'res_model': 'wua.watermeter',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.watermeter_ids.ids)],
            'context': {'default_zone_id': self.id}
            }
        return act_window
