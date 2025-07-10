# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools, _


class ResPartnerWaterconnection(models.Model):
    _inherit = 'res.partner.waterconnection'

    last_reading_time = fields.Datetime(
        string='Last Reading Time',
    )

    last_reading_value = fields.Float(
        string='Last Reading Value',
        digits=(32, 4),
    )

    is_state_close = fields.Boolean(
        string='State Close',
        related='waterconnection_id.is_state_close',
    )

    watermeter_id = fields.Many2one(
        string='Watermeter',
        comodel_name='wua.watermeter',
        related='waterconnection_id.watermeter_id',)

    volume_real = fields.Float(
        string='Consumption (m³)',
        digits=(32, 4),)

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='res_partner_waterconnection')
            """)
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(self.env.cr,
                                      'res_partner_waterconnection')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                CREATE OR REPLACE VIEW res_partner_waterconnection AS (
                SELECT row_number() OVER() AS id, a.* FROM (
                    SELECT wpp1.partner_id, wpi1.waterconnection_id,
                    wpi1.active,
                    ww1.last_reading_time, ww1.last_reading_value,
                    wpc1.volume_real
                    FROM
                    wua_parcel_irrigationpoint wpi1
                    INNER JOIN  wua_waterconnection ww1
                    ON ww1.id = wpi1.waterconnection_id
                    INNER JOIN wua_parcel_partnerlink wpp1
                    ON wpp1.parcel_id = wpi1.parcel_id
                    LEFT JOIN wua_presconsumption wpc1
                    ON wpc1.waterconnection_id = ww1.id
                    AND wpc1.reading_end_time = ww1.last_reading_time
                    WHERE wpi1.type='WC' AND ww1.watermeter_id IS NOT NULL
                    GROUP BY  wpp1.partner_id, wpi1.waterconnection_id,
                     wpi1.active,
                    ww1.last_reading_time, ww1.last_reading_value,
                    wpc1.volume_real
                    ORDER BY wpp1.partner_id, wpi1.waterconnection_id,
                    ww1.last_reading_time
                ) a )
                """)
        except Exception:
            self.env.cr.rollback()

    def action_show_watermeter_id(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.wua_watermeter_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Watermeter'),
            'res_model': 'wua.watermeter',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.watermeter_id.id
            }
        return act_window
