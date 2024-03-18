# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    watermeter_model = env['wua.watermeter']
    reading_model = env['wua.reading']
    watermeters = watermeter_model.search([])
    for record in watermeters:
        reading = reading_model.search([('watermeter_id', '=', record.id)],
                                       order='reading_time DESC', limit=1)
        if reading:
            record.last_reading_consumption = \
                reading.presconsumption_volume_real
        else:
            record.last_reading_consumption = 0
