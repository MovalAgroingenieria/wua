# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.configuration' AND
            (name='show_sign' OR
            name='page_of_signature' OR
            name='llx_for_signature' OR
            name='lly_for_signature' OR
            name='urx_for_signature' OR
            name='ury_for_signature' OR
            name='max_signatures' OR
            name='column_spacing' OR
            name='fit_image')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
