# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, _, exceptions


def pre_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    resp = False
    env.cr.execute("""
        SELECT EXISTS(SELECT * FROM pg_extension WHERE extname='postgis')
        AND EXISTS(SELECT * FROM information_schema.schemata  WHERE
                    schema_name='postgis')
        """)
    result = env.cr.fetchone()[0]
    if result and result != 'f':
        resp = True
    if (not resp):
        raise exceptions.ValidationError(_(
            'PostGIS not installed. Please contact your administrator to '
            'install it before proceeding.'))
