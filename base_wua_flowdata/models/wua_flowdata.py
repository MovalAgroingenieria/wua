# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaFlowData(models.Model):
    _name = 'wua.flowdata'
    _description = 'Flow Data'
    _order = 'time desc'

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS (SELECT extname FROM pg_extension
            WHERE extname = 'timescaledb');""")
        timescaledb_is_installed = self.env.cr.fetchone()[0]
        if timescaledb_is_installed:
            # Hypertable
            self.env.cr.execute("""
                ALTER TABLE wua_flowdata
                DROP CONSTRAINT IF EXISTS wua_flowdata_pkey;""")
            self.env.cr.commit()
            self.env.cr.execute("""
                SELECT create_hypertable('wua_flowdata','time',
                if_not_exists => TRUE, migrate_data => TRUE);""")
            self.env.cr.commit()

            # Indexes
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS wua_flowdata_flowmeter_time_idx
                ON wua_flowdata (flowmeter_id, time DESC);
                CREATE INDEX IF NOT EXISTS wua_flowdata_id_time_idx
                ON wua_flowdata (id, time DESC);""")
            self.env.cr.commit()

            # Materialized views
            self.env.cr.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS wua_flowdata_hourly
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 hour', "time") AS hour,
                    flowmeter_id,
                    max(flow) AS max,
                    min(flow) AS min,
                    avg(flow) AS average
                FROM wua_flowdata srt
                GROUP BY hour, flowmeter_id
                WITH NO DATA;;""")
            self.env.cr.commit()
            self.env.cr.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS wua_flowdata_daily
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 day', "time") AS day,
                    flowmeter_id,
                    max(flow) AS max,
                    min(flow) AS min,
                    avg(flow) AS average
                FROM wua_flowdata srt
                GROUP BY day, flowmeter_id
                WITH NO DATA;;""")
            self.env.cr.commit()
            self.env.cr.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS wua_flowdata_weekly
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('7 day', "time") AS week,
                    flowmeter_id,
                    max(flow) AS max,
                    min(flow) AS min,
                    avg(flow) AS average
                FROM wua_flowdata srt
                GROUP BY week, flowmeter_id
                WITH NO DATA;;""")
            self.env.cr.commit()
            self.env.cr.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS wua_flowdata_monthly
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('30 day', "time") AS month,
                    flowmeter_id,
                    max(flow) AS max,
                    min(flow) AS min,
                    avg(flow) AS average
                FROM wua_flowdata srt
                GROUP BY month, flowmeter_id
                WITH NO DATA;;""")
            self.env.cr.commit()

            # Aggregate policies
            self.env.cr.execute("""
                SELECT add_continuous_aggregate_policy('wua_flowdata_hourly',
                  start_offset => INTERVAL '7 days',
                  end_offset => INTERVAL '5 min',
                  schedule_interval => INTERVAL '1 hours',
                  if_not_exists => TRUE);""")
            self.env.cr.commit()
            self.env.cr.execute("""
                SELECT add_continuous_aggregate_policy('wua_flowdata_daily',
                  start_offset => INTERVAL '7 days',
                  end_offset => INTERVAL '1 hour',
                  schedule_interval => INTERVAL '1 days',
                if_not_exists => TRUE);""")
            self.env.cr.commit()
            self.env.cr.execute("""
                SELECT add_continuous_aggregate_policy('wua_flowdata_weekly',
                  start_offset => INTERVAL '1 month',
                  end_offset => INTERVAL '1 hour',
                  schedule_interval => INTERVAL '1 week',
                if_not_exists => TRUE);""")
            self.env.cr.commit()
            self.env.cr.execute("""
                SELECT add_continuous_aggregate_policy('wua_flowdata_monthly',
                  start_offset => INTERVAL '3 month',
                  end_offset => INTERVAL '1 hour',
                  schedule_interval => INTERVAL '1 month',
                if_not_exists => TRUE);""")
            self.env.cr.commit()

            # Compression (Not used)
            # self.env.cr.execute("""
            #     ALTER TABLE wua_flowdata SET (
            #       timescaledb.compress,
            #       timescaledb.compress_orderby = 'time DESC',
            #       timescaledb.compress_segmentby = 'flowmeter_id');""")
            # self.env.cr.commit()
            # self.env.cr.execute("""
            #     SELECT add_compression_policy(
            #         'wua_flowdata', INTERVAL '7 days');""")
            # self.env.cr.commit()

    name = fields.Char(
        string='Identifier',
        size=30,
        required=True,
        compute="_compute_name")

    # Indexed by TimescaleDB
    time = fields.Datetime(
        string="Time",
        required=True)

    flow = fields.Float(
        string="Flow (l/s)",
        digits=(32, 4),
        required=True)

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter')

    @api.depends('flowmeter_id', 'time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.flowmeter_id and record.time:
                name = record.flowmeter_id.name + '-' + record.time
            record.name = name

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            flowmeter_name = record.flowmeter_id.name
            time = fields.Datetime.from_string(record.time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(time)
                time = time + offset
            time_str = str(time)
            date_str = time_str[:10]
            hour_str = time_str[-8:]
            name = flowmeter_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result
