# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    # Actualizar el dominio de la acción automática
    cr.execute("""
        UPDATE base_action_rule
        SET filter_domain = '[("requested_from_portal", "=", True)]'
        WHERE id = (SELECT res_id FROM ir_model_data WHERE module = 'base_wua_certificate' AND name = 'action_rule_send_email_on_certificate_creation')
    """)
