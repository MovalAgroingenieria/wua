# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardActivateSeason(models.TransientModel):
    _name = 'wizard.activate.season'
    _description = 'Wizard to activate a season and mass-create crop units '\
                   'and/or monitoring periods'

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason')

    agriculturalseason_description = fields.Char(
        string='Description of the agricultural season',
    )

    is_periodicity_weekly = fields.Boolean(
        string='Weekly Periodicity (y/n)',
    )

    number_of_monitoringperiods = fields.Integer(
        string='Number of control periods',
    )

    number_of_cropunits = fields.Integer(
        string='Number of crop units',
    )

    option_create_monitoringperiods = fields.Selection(
        string='Options for bulk creation of control periods',
        selection=[
            ('01_automatic', 'Create weekly control periods automatically'),
            ('02_none', 'Do not create any control period')
        ],
    )

    option_create_cropunits = fields.Selection(
        string='Options for bulk creation of crop units',
        selection=[
            ('01_previous_season', 'Create them from the previous season'),
            ('02_sigpac_enclosures', 'Create them from SIGPAC enclosures'),
            ('03_parcels', 'Create them from parcels'),
            ('04_none', 'Do not create any crop unit')
        ],
    )

    @api.multi
    def _compute_is_periodicity_weekly(self):
        control_periodicity = self.env['ir.values'].get_default(
            'wua.configuration', 'control_periodicity')
        if not control_periodicity:
            control_periodicity = 7
        print control_periodicity
        for record in self:
            record.is_periodicity_weekly = (control_periodicity == 7)

    @api.multi
    def _compute_number_of_monitoringperiods(self):
        for record in self:
            number_of_monitoringperiods = 0
            if record.agriculturalseason_id:
                number_of_monitoringperiods = \
                    record.number_of_monitoringperiods
            record.number_of_monitoringperiods = number_of_monitoringperiods

    @api.multi
    def _compute_number_of_cropunits(self):
        for record in self:
            number_of_cropunits = 0
            if record.agriculturalseason_id:
                number_of_cropunits = \
                    record.number_of_cropunits
            record.number_of_cropunits = number_of_cropunits

    @api.model
    def default_get(self, var_fields):
        agriculturalseason_id = None
        agriculturalseason_description = ''
        is_periodicity_weekly = True
        number_of_monitoringperiods = 0
        number_of_cropunits = 0
        option_create_monitoringperiods = '02_none'
        option_create_cropunits = '04_none'
        active_id = self.env.context['active_id']
        if active_id:
            agriculturalseason = self.env['wua.agriculturalseason'].browse(
                active_id)
            if agriculturalseason:
                agriculturalseason_id = agriculturalseason.id
                agriculturalseason_description = \
                    agriculturalseason.description.upper()
                control_periodicity = self.env['ir.values'].get_default(
                    'wua.configuration', 'control_periodicity')
                if control_periodicity and control_periodicity != 7:
                    is_periodicity_weekly = False
                number_of_monitoringperiods = \
                    agriculturalseason.number_of_monitoringperiods
                number_of_cropunits = \
                    agriculturalseason.number_of_cropunits
                if is_periodicity_weekly and number_of_monitoringperiods == 0:
                    option_create_monitoringperiods = '01_automatic'
        return {
            'agriculturalseason_id': agriculturalseason_id,
            'agriculturalseason_description': agriculturalseason_description,
            'is_periodicity_weekly': is_periodicity_weekly,
            'number_of_monitoringperiods': number_of_monitoringperiods,
            'number_of_cropunits': number_of_cropunits,
            'option_create_monitoringperiods': option_create_monitoringperiods,
            'option_create_cropunits': option_create_cropunits,
        }

    def activate_agriculturalseason(self):
        if self.agriculturalseason_id:
            season = self.agriculturalseason_id
            model_wua_agriculturalseason = self.env['wua.agriculturalseason']
            previous_active_seasons = model_wua_agriculturalseason.search(
                [('active_agriculturalseason', '=', True)])
            for previous_active_season in (previous_active_seasons or []):
                previous_active_season.deactivate()
            season.write({'active_agriculturalseason': True})
            if self.option_create_monitoringperiods == '01_automatic':
                season.generate_weekly_periods()
            if self.option_create_cropunits == '01_previous_season':
                season.generate_cropunits_from_prev_season()
            elif self.option_create_cropunits == '02_sigpac_enclosures':
                season.generate_cropunits_from_sigpac_enclosures()
            elif self.option_create_cropunits == '03_parcels':
                season.generate_cropunits_from_parcels()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }
