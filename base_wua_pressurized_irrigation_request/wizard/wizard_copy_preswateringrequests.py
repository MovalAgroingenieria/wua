# -*- coding: utf-8 -*-
# Copyright 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WizardCopyPreswateringrequests(models.TransientModel):
    _name = 'wizard.copy.preswateringrequests'
    _description = 'Wizard to Copy Pressurized Watering Requests'

    preswateringperiod_id = fields.Many2one(
        comodel_name='wua.preswateringperiod',
        string='Period',
        required=True,
    )

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
    )

    interval_days = fields.Integer(
        string='Copy Interval (days)',
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(WizardCopyPreswateringrequests, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            preswateringrequest = \
                self.env['wua.preswateringrequest'].browse(active_ids[0])
            if preswateringrequest:
                res.update({
                    'preswateringperiod_id':
                        preswateringrequest.preswateringperiod_id.id,
                    'initial_date':
                        preswateringrequest.preswateringperiod_id.initial_date,
                    'end_date':
                        preswateringrequest.preswateringperiod_id.end_date,
                    'interval_days': 30,
                })
        return res

    @api.multi
    def copy_requests(self):
        self.ensure_one()
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('The dates are incorrect.'))
        if self.interval_days <= 0:
            raise exceptions.UserError(
                _('The interval must be greater than 0.'))
        if (self.initial_date < self.preswateringperiod_id.initial_date or
                self.end_date > self.preswateringperiod_id.end_date):
            raise exceptions.UserError(
                _('The date range must be within the watering period.'))
        preswateringrequests = self.env['wua.preswateringrequest'].browse(
            self.env.context['active_ids'])
        current_date = datetime.strptime(str(self.initial_date), '%Y-%m-%d')
        end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d')
        while current_date <= end_date:
            for request in preswateringrequests:
                self.env['wua.preswateringrequest'].\
                    _copy_single_request(request, current_date)
            current_date += timedelta(days=self.interval_days)
