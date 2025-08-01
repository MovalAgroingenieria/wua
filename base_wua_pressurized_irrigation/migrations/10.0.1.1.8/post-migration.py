# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import api, fields, SUPERUSER_ID


def migrate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Migration logic for watermeters without initialization readings
    watermeter_model = env['wua.watermeter']
    reading_model = env['wua.reading']
    # Find all watermeters that have a waterconnection but no readings
    watermeters_with_wc = watermeter_model.search([
        ('waterconnection_id', '!=', False),
    ])
    current_date = datetime.datetime.now()
    for watermeter in watermeters_with_wc:
        # Check if the watermeter has any readings
        existing_readings = reading_model.search([
            ('watermeter_id', '=', watermeter.id),
        ], limit=1)
        # if no readings exist, create an initialization reading
        if not existing_readings:
            last_reading_time = current_date
            last_reading_value = 0
            last_reading_consumption = 0
            # Use existing values from watermeter if available
            if watermeter.last_reading_time:
                last_reading_time = str(
                    fields.Datetime.from_string(watermeter.last_reading_time) +
                    datetime.timedelta(seconds=1))
            if watermeter.last_reading_value:
                last_reading_value = watermeter.last_reading_value
            if watermeter.last_reading_consumption:
                last_reading_consumption = watermeter.last_reading_consumption
            vals_new_initialization_reading = {
                'watermeter_id': watermeter.id,
                'reading_time': last_reading_time,
                'volume': last_reading_value,
                'volume_real': last_reading_consumption,
                'initialization_reading': True,
            }
            reading_model.create(vals_new_initialization_reading)
