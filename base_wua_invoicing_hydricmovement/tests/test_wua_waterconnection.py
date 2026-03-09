# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaWaterconnectionHydricmovement(SavepointCase):
    post_install = True

    def test_compute_last_invoiced_presconsumption_empty_recordset_no_error(self):
        self.env['wua.waterconnection']._compute_last_invoiced_presconsumption()
