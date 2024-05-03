# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, exceptions, _


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Initial condition: db_link is installed
    exists_dblink_extension = False
    try:
        env.cr.execute(
            'SELECT true AS installed FROM pg_available_extensions WHERE '
            'name=\'dblink\' AND installed_version IS NOT NULL LIMIT 1;')
        query_results = env.cr.dictfetchall()
        if (query_results and query_results[0].get('installed') == 't'):
            exists_dblink_extension = True
    except Exception:
        exists_dblink_extension = False
    if not exists_dblink_extension:
        try:
            env.cr.execute('CREATE EXTENSION dblink;')
        except Exception:
            raise exceptions.MissingError(
                _('ATTENTION: it is not possible to install this module, '
                  'because the dblink postgres extension cannot be '
                  'installed.'))
