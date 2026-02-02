# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models, fields, api, exceptions, _


class WizardCropunitClose(models.TransientModel):
    _name = 'wizard.cropunit.close'
    _description = 'Wizard to close or change end date of crop units'

    end_date = fields.Date(
        string='New End Date',
        required=True,
        default=fields.Date.today,
        help='Set the new end date for the selected crop units. '
             'Crop units will be automatically marked as finished if the end date is in the past.',
    )

    cropunit_count = fields.Integer(
        string='Number of Crop Units',
        compute='_compute_cropunit_count',
    )

    result_message = fields.Text(
        string='Result',
        readonly=True,
    )

    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Done')],
        default='draft',
    )

    @api.depends('end_date')
    def _compute_cropunit_count(self):
        for record in self:
            cropunit_ids = self.env.context.get('active_ids', [])
            record.cropunit_count = len(cropunit_ids)

    @api.multi
    def action_apply(self):
        self.ensure_one()

        cropunit_ids = self.env.context.get('active_ids', [])
        if not cropunit_ids:
            raise exceptions.Warning(_('No crop units selected.'))

        cropunits = self.env['wua.cropunit'].browse(cropunit_ids)
        invalid_cropunits = []
        for cropunit in cropunits:
            if cropunit.initial_date and self.end_date < cropunit.initial_date:
                invalid_cropunits.append(cropunit.name)

        if invalid_cropunits:
            raise exceptions.ValidationError(
                _('The end date cannot be earlier than the initial date for the following crop units:\n%s') %
                '\n'.join(invalid_cropunits)
            )
        cropunits.write({'end_date': self.end_date})
        cropunits._compute_state()
        closed_count = len(cropunits.filtered(lambda c: c.state == '03_closed'))
        active_count = len(cropunits.filtered(lambda c: c.state == '02_active'))
        not_started_count = len(cropunits.filtered(lambda c: c.state == '01_not_started'))
        message = _('End date updated for %d crop unit(s):') % len(cropunits)
        message += '\n\n'
        if closed_count > 0:
            message += _('- %d crop unit(s) marked as finished\n') % closed_count
        if active_count > 0:
            message += _('- %d crop unit(s) still active\n') % active_count
        if not_started_count > 0:
            message += _('- %d crop unit(s) not started yet\n') % not_started_count
        self.write({
            'state': 'done',
            'result_message': message,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.cropunit.close',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    @api.multi
    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
