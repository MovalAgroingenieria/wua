# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Protect Spherag ir.values defaults from recreation and duplicates."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_values = env['ir.values'].sudo()
    model_data = env['ir.model.data'].sudo()
    setting_names = [
        'url_remotecontrol_application_spherag',
        'automatic_census_synchronization_spherag',
        'can_be_sent_partners_census_spherag',
        'can_be_sent_parcels_census_spherag',
        'import_from_readings_spherag',
        'import_from_waterconnection_spherag',
        'import_from_irrigationshed_spherag',
        'import_from_hydraulicsector_spherag',
        'spherag_default_hydraulicsector_id',
    ]
    xmlids = [
        'param_ir_values_url_remotecontrol_application_spherag',
        'param_ir_values_automatic_census_synchronization_spherag',
        'param_ir_values_can_be_sent_partners_census_spherag',
        'param_ir_values_can_be_sent_parcels_census_spherag',
        'param_ir_values_import_from_readings_spherag',
        'param_ir_values_import_from_waterconnection_spherag',
        'param_ir_values_import_from_irrigationshed_spherag',
        'param_ir_values_import_from_hydraulicsector_spherag',
        'param_ir_values_spherag_default_hydraulicsector_id',
    ]

    # Ensure these XML records are applied on future module updates.
    model_data_records = model_data.search([
        ('module', '=', 'wua_remotecontrol_rest_spherag'),
        ('name', 'in', xmlids),
    ])
    if model_data_records:
        model_data_records.write({'noupdate': False})
    # Keep latest value and remove duplicates for each protected setting.
    config_values = ir_values.search([
        ('model', '=', 'wua.irrigation.configuration'),
        ('name', 'in', setting_names),
    ], order='id desc')
    if not config_values:
        return
    seen_keys = {}
    to_delete = []
    for record in config_values:
        key = (record.model, record.key, record.name)
        if key in seen_keys:
            to_delete.append(record.id)
            continue
        seen_keys[key] = record.id

    if to_delete:
        ir_values.browse(to_delete).unlink()
