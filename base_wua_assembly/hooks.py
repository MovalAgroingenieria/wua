# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    companies = env['res.company'].search([])
    if companies and len(companies) == 1:
        company = companies[0].partner_id
        if company.street:
            values.set_default('wua.assembly.configuration',
                               'assembly_street', company.street)
        if company.zip:
            values.set_default('wua.assembly.configuration',
                               'assembly_zip', company.zip)
        if company.city:
            values.set_default('wua.assembly.configuration',
                               'assembly_city', company.city)
        if company.state_id:
            values.set_default('wua.assembly.configuration',
                               'assembly_state_id', company.state_id.id)
        if company.country_id:
            values.set_default('wua.assembly.configuration',
                               'assembly_country_id', company.country_id.id)
    values.set_default('wua.assembly.configuration',
                       'assembly_president_id', 1)
    values.set_default('wua.assembly.configuration',
                       'assembly_secretary_id', 1)
    values.set_default('wua.assembly.configuration',
                       'vat_required', False)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.assembly.configuration' AND
            (name='assembly_street' OR name='assembly_zip' OR
            name='assembly_city' OR name='assembly_state_id' OR
            name='assembly_country_id' OR name='assembly_president_id' OR
            name='assembly_secretary_id' OR
            name='vat_required')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
