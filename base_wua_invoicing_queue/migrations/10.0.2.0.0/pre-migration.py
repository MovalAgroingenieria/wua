# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "UPDATE wua_invoiceset "
        "SET calculate_in_progress = false "
        "WHERE calculate_in_progress = true")
