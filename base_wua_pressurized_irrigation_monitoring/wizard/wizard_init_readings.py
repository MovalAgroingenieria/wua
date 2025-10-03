from odoo import models, fields


class WizardInitReadingControl(models.TransientModel):
    _inherit = 'wizard.init.reading'

    create_control_readings = fields.Boolean(
        string="Create control readings",
    )

    def action_generate_init_readings(self):
        self.ensure_one()
        wc = self.waterconnection_id
        if not wc.watermeter_id:
            raise exceptions.UserError(
                _('This waterconnection has no watermeter assigned.')
            )
        vals = {
            'watermeter_id': wc.watermeter_id.id,
            'waterconnection_id': wc.id,
            'date': self.date_change,
            'final_value': self.final_reading,
            'init_value': self.initial_reading,
            'notes': self.notes,
        }
        self._create_readings_in_model('wua.reading', vals)
        if self.create_control_readings:
            self._create_readings_in_model('wua.controlreading', vals)
        return {'type': 'ir.actions.act_window_close'}