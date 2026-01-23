# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, fields, api, exceptions, _


class WizardGenerateMonitoringperiods(models.TransientModel):
    _name = 'wizard.generate.monitoringperiods'
    _description = 'Dialog box to generate control periods'

    agriculturalseason_name = fields.Char(
        string='Agricultural Season',
        readonly=True,
    )

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
    )

    @api.model
    def default_get(self, var_fields):
        current_agriculturalseason_data = \
            self.get_current_agriculturalseason_data()
        return current_agriculturalseason_data

    @api.multi
    def generate_periods(self):
        self.ensure_one()
        logging.getLogger(__name__).info(
            '>>> WIZARD generate_monitoringperiods: Iniciando generación')
        if len(self.env.context.get('active_ids', [])) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context.get('active_id'))
        if not agriculturalseason:
            raise exceptions.UserError(_('No agricultural season selected.'))
        logging.getLogger(__name__).info(
            '    Temporada seleccionada: %s (ID=%s)',
            agriculturalseason.name, agriculturalseason.id)
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates.'))
        if (self.initial_date < agriculturalseason.initial_date or
           self.end_date > agriculturalseason.end_date):
            raise exceptions.UserError(_(
                'The range of dates must be within the agricultural season.'))
        if agriculturalseason.number_of_monitoringperiods > 0:
            raise exceptions.UserError(_(
                'Control periods already exist for this season. '
                'Please delete them first if you want to regenerate.'))
        logging.getLogger(__name__).info(
            '    Llamando a generate_weekly_periods...')
        try:
            agriculturalseason.generate_weekly_periods()
            logging.getLogger(__name__).info(
                '    Periodos generados correctamente')
        except Exception as e:
            logging.getLogger(__name__).error(
                '    ERROR generando periodos: %s', str(e))
            raise
        return {'type': 'ir.actions.act_window_close'}

    def get_current_agriculturalseason_data(self):
        agriculturalseason_name = ''
        initial_date = fields.datetime.now()
        end_date = initial_date
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context.get('active_id'))
        if agriculturalseason:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                agriculturalseason.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                agriculturalseason.end_date)
            if agriculturalseason.description:
                agriculturalseason_name = (
                    initial_date_str + ' - ' + end_date_str + ' ' +
                    '[' + agriculturalseason.description + ']')
            else:
                agriculturalseason_name = initial_date_str + ' - ' + end_date_str

            initial_date = agriculturalseason.initial_date
            end_date = agriculturalseason.end_date

        return {
            'agriculturalseason_name': agriculturalseason_name,
            'initial_date': initial_date,
            'end_date': end_date,
        }
