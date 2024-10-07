# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardEditReadingTime(models.TransientModel):
    _name = 'wizard.edit.reading.time'
    _description = 'Dialog box to edit reading time'

    def _default_reading_ids(self):
        active_ids = self.env.context.get('active_ids')
        return [(6, 0, active_ids)] if active_ids else []

    new_reading_time = fields.Datetime(
        string='Initial Date',
        required=True,
    )

    reading_ids = fields.Many2many(
        string="Readings",
        comodel_name='wua.reading',
        default=_default_reading_ids,
    )

    incorrect_reading_msg = fields.Html(
        string="Incorrect Readings Message",
        compute='_compute_incorrect_reading_msg',
    )

    @api.onchange('reading_ids', 'new_reading_time')
    @api.multi
    def _compute_incorrect_reading_msg(self):
        for record in self:
            incorrect_reading_msg = ''
            if (record.reading_ids):
                incorrect_readings = record.reading_ids.filtered(
                    lambda x: (not x.is_last_reading) or (x.validated),
                ).mapped('name')
                if (len(incorrect_readings) > 0):
                    incorrect_reading_msg += _(
                        '<span>Some readings are not gonna be modified:'
                        '</span><br/>')
                    incorrect_reading_msg += '<br/>'.join(incorrect_readings)
            record.incorrect_reading_msg = incorrect_reading_msg

    @api.multi
    def edit_reading_time(self):
        self.ensure_one()
        for reading in self.reading_ids:
            if (reading.is_last_reading and not reading.validated):
                previous_reading = self.env['wua.reading'].search(
                    [('watermeter_id', '=', reading.watermeter_id.id),
                     ('reading_time', '<', reading.reading_time)],
                    limit=1, order='reading_time desc')
                if (previous_reading and previous_reading.reading_time >=
                        self.new_reading_time):
                    raise exceptions.UserError(
                        _('The new reading time for reading "%s" (%s) is '
                          'earlier than the last reading time (%s).') %
                        (reading.name, self.new_reading_time,
                         previous_reading.reading_time),
                    )
                reading.write({
                    'reading_time': self.new_reading_time,
                })
                # Volume for watermeter if last_reading, then 0
                volume_real = 0
                if (reading.presconsumption_id):
                    reading.presconsumption_id.write({
                        'reading_end_time': self.new_reading_time,
                    })
                    volume_real = reading.presconsumption_id.volume_real
                if (reading.watermeter_id):
                    vals_watermeter = {
                        'last_reading_time': self.new_reading_time,
                        'last_reading_value': reading.volume,
                        'last_reading_consumption': volume_real}
                    reading.watermeter_id.write(vals_watermeter)
