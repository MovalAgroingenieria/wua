# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WuaParcelSensorReading(models.Model):

    _name = 'wua.parcel.sensor.reading'
    _auto = False
    _order = 'name'

    name = fields.Char(
        string='Identifier of parcel sensor-reading',
        readonly=True)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        readonly=True)

    device_id = fields.Many2one(
        string='Device',
        comodel_name='mdm.measurement.device',
        readonly=True)

    sensor_id = fields.Many2one(
        string='Sensor',
        comodel_name='mdm.measurement.device.sensor',
        readonly=True)

    type_id = fields.Many2one(
        string='Sensor Type',
        comodel_name='mdm.measurement.device.sensor.type',
        readonly=True)

    reading_id = fields.Many2one(
        string='Reading',
        comodel_name='mdm.measurement.device.sensor.reading',
        readonly=True)

    measurement_time = fields.Datetime(
        string='Measurement Time',
        readonly=True)

    value = fields.Float(
        string='Value',
        readonly=True)

    uom_id = fields.Many2one(
        string='Unit of Measure',
        comodel_name='mdm.measurement.device.sensor.uom',
        readonly=True)

    @api.model
    def refresh_materialized_view(self):
        from odoo import sql_db
        db_name = self.env.cr.dbname
        new_cr = sql_db.db_connect(db_name).cursor()

        try:
            new_cr.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY wua_parcel_sensor_reading;")
            new_cr.commit()
        except Exception:
            new_cr.rollback()
            try:
                new_cr.execute("REFRESH MATERIALIZED VIEW wua_parcel_sensor_reading;")
                new_cr.commit()
            except Exception:
                new_cr.rollback()
                raise
        finally:
            new_cr.close()
