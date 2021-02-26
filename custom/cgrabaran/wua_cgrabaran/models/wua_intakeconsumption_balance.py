# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from lxml import etree
from odoo import models, tools, fields, api, _, exceptions


class WuaIntakeconsumptionBalance(models.Model):

    _name = 'wua.intakeconsumption.balance'
    _description = 'Entity (intakeconsumption balance)'

    MAX_SIZE_NAME = 27
    MAX_SIZE_DESCRIPTION = 75

    name = fields.Char(
        string='Intakeconsumption Balance',
        index=True,
        store=True,
        compute="_compute_name",
        size=MAX_SIZE_NAME)

    description = fields.Char(
        string='Description',
        required=True,
        size=MAX_SIZE_DESCRIPTION)

    balance_type = fields.Selection([
        ('C', 'Agricultural Season'),
        ('R', 'Date Range'),
        ],
        string='Balance Type',
        default='C',
        required=True)

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='cascade')

    date_range_id = fields.Many2one(
        string='Date Range',
        comodel_name='date.range',
        index=True,
        ondelete='cascade')

    balance_month_ids = fields.One2many(
        string='Balance Months',
        comodel_name='wua.intakeconsumption.balance.month',
        inverse_name='balance_id',)

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing Intakeconsumption balance identifier.'),
    ]

    @api.onchange('agriculturalseason_id', 'date_range_id')
    def _onchage_agriculturalseason_date_range(self):
        start_date = ''
        end_date = ''
        if (self.balance_type == 'C' and self.agriculturalseason_id):
            start_date = self.agriculturalseason_id.initial_date
            end_date = self.agriculturalseason_id.end_date
        elif (self.balance_type == 'R' and self.date_range_id):
            start_date = self.date_range_id.date_start
            end_date = self.date_range_id.date_end
        if (start_date and end_date):
            initial_date_str = datetime.datetime.strptime(
                start_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                end_date, '%Y-%m-%d').strftime('%x')
            self.description = initial_date_str + ' - ' + end_date_str

    @api.depends('balance_type', 'agriculturalseason_id', 'date_range_id')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.balance_type == 'R' and record.date_range_id):
                name = record.balance_type + ' - ' + \
                    record.date_range_id.date_start + ' - ' + \
                    record.date_range_id.date_end
            elif (record.balance_type == 'C' and record.agriculturalseason_id):
                name = record.balance_type + ' - ' + \
                    record.agriculturalseason_id.initial_date + ' - ' + \
                    record.agriculturalseason_id.end_date
            record.name = name

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = False
        if self.env.context and 'lang' in self.env.context:
            is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            start_date = ''
            end_date = ''
            if (record.balance_type == 'C'):
                start_date = record.agriculturalseason_id.initial_date
                end_date = record.agriculturalseason_id.end_date
            elif (record.balance_type == 'R'):
                start_date = record.date_range_id.date_start
                end_date = record.date_range_id.date_end
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    start_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def action_see_sum_intakeconsumption_invoicing(self):
        self.ensure_one()
        condition = [('balance_id', '=', self.id)]
        id_tree_view = self.env.ref('wua_cgrabaran.'
                                    'wua_sum_intakeconsumption_invoicing_view'
                                    '_tree').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumption balance'),
            'res_model': 'wua.sum.intakeconsumption.invoicing',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.model
    def create(self, vals):
        if (vals['balance_type'] == 'C'):
            if ('agriculturalseason_id' not in vals or
                    not vals['agriculturalseason_id']):
                raise exceptions.UserError(_('Agriculturalseason is '
                                             'mandatory.'))
        if (vals['balance_type'] == 'R'):
            if ('date_range_id' not in vals or not vals['date_range_id']):
                raise exceptions.UserError(_('Date Range is mandatory.'))
        balance_created =  \
            super(WuaIntakeconsumptionBalance, self).create(vals)
        if balance_created:
            if (balance_created.balance_type == 'R'):
                start_date = fields.Datetime.from_string(
                    balance_created.date_range_id.date_start)
                end_date = fields.Datetime.from_string(
                    balance_created.date_range_id.date_end)
            else:
                start_date = fields.Datetime.from_string(
                    balance_created.agriculturalseason_id.initial_date)
                end_date = fields.Datetime.from_string(
                    balance_created.agriculturalseason_id.end_date)
                balance_created.agriculturalseason_id.balance_id = \
                    balance_created
            start_year = start_date.year
            start_month = start_date.month
            end_year = end_date.year
            end_month = end_date.month
            number_of_months = end_month - start_month + 12 * \
                (end_year - start_year)
            for month in range(0, number_of_months + 1):
                year_overflow = 0
                month_fixed = start_month + month
                if (month_fixed > 12):
                    month_fixed = month_fixed % 12
                    year_overflow = (start_month + month) / 12
                    if (month_fixed == 0):
                        month_fixed = 12
                        year_overflow -= 1
                self.env['wua.intakeconsumption.balance.month'].create({
                    'balance_id': balance_created.id,
                    'month': month_fixed,
                    'year': start_year + year_overflow
                    })
        return balance_created

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_sum_intakeconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_intakeconsumption AS (
            SELECT row_number() OVER() AS id, a.* FROM (SELECT
            wi1.company_id AS company_id, iv1.name AS company,
            extract (month FROM ((wic1.reading_initial_time AT TIME ZONE 'UTC')
            AT TIME ZONE 'Europe/Madrid')) AS month,
            extract(year from ((wic1.reading_initial_time AT TIME ZONE 'UTC')
            AT TIME ZONE 'Europe/Madrid')) AS year, sum(wic1.volume_real) AS
            volume_total FROM wua_intakeconsumption wic1
            LEFT JOIN wua_intake wi1 ON wi1.id = wic1.intake_id LEFT JOIN
            ir_values iv1 ON wi1.company_id = (CAST(substring(iv1.value from
            \'\\d\') AS INTEGER)) where iv1.model = 'wua.configuration' and
            (iv1.name = 'company_01' OR iv1.name = 'company_02' OR iv1.name =
            'company_03') AND validated AND wi1.company_id IS NOT NULL GROUP BY
            year, month, iv1.name, wi1.company_id
            ORDER BY iv1.name, year, month)
             a)
            """)
        tools.drop_view_if_exists(self.env.cr, 'wua_sum_invoicing')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_invoicing AS (
            SELECT row_number() OVER() AS id, a.* FROM
            (
            SELECT b.company_id, b.company as company, extract
            (year FROM ((b.date_invoice AT TIME ZONE 'UTC' ) AT
            TIME ZONE 'Europe/Madrid')) AS year,
            extract (month FROM ((b.date_invoice AT TIME ZONE 'UTC' ) AT
            TIME ZONE 'Europe/Madrid')) AS month,
            SUM(b.quantity) AS total_quantity FROM
                (
                SELECT a1.company_id as company_id, iv1.name as company,
                CASE
                    WHEN p1.productcategory_code = 11 AND pu1.name = 'Hour(s)'
                    THEN a1.quantity * (SELECT CAST(substring(value
                                        FROM \'\\d+.?\\d+?\') AS FLOAT) FROM
                                        ir_values where model =
                                        'wua.configuration' AND name =
                                        'volume_time_equivalence')
                ELSE a1.quantity
                END as quantity,
                CASE
                    WHEN p1.productcategory_code = 11
                    THEN (SELECT wi1.report_end_time FROM wua_irrigationreport
                          wi1 WHERE wi1.id = a1.irrigationreport_id)
                    ELSE TO_TIMESTAMP(substring(a1.name,
                    \'Lectura final: (\\d+/\\d+/\\d\\d)\'), 'DD/MM/YY') AT
                    TIME ZONE \'UTC\'
                END
                AS date_invoice FROM
                    account_invoice_line a1
                    INNER JOIN product_category p1
                    ON a1.categ_id = p1.id
                    INNER JOIN product_uom pu1
                    ON a1.uom_id = pu1.id
                    INNER JOIN ir_values iv1
                    ON a1.company_id = (CAST(substring(iv1.value from \'\\d\')
                                       AS INTEGER)) WHERE iv1.model =
                                       'wua.configuration' and
                                       (iv1.name = 'company_01' OR
                                        iv1.name = 'company_02' OR
                                        iv1.name = 'company_03') AND
                                       (p1.productcategory_code = 7 OR
                                        p1.productcategory_code = 11)
                    ) b
            GROUP BY b.company_id, year, month, b.company
            ORDER BY b.company, year, month
            ) a)
            """)


class WuaIntakeconsumptionBalanceMonth(models.Model):

    _name = 'wua.intakeconsumption.balance.month'
    _description = 'Entity (intakeconsumption balance month)'

    balance_id = fields.Many2one(
        string='Balance',
        comodel_name='wua.intakeconsumption.balance',
        index=True,
        ondelete='cascade',
        required=True)

    year = fields.Integer(
        string='Year',
        required=True)

    month = fields.Integer(
        string='Month',
        required=True)

    sum_intakeconsumption_company_01 = fields.Float(
        string='Total Intake Consumptions of Company 01',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_01 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 01',
        default=0.0,
        digits=(32, 4))

    sum_intakeconsumption_company_02 = fields.Float(
        string='Total Intake Consumptions of Company 02',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_02 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 02',
        default=0.0,
        digits=(32, 4))

    sum_intakeconsumption_company_03 = fields.Float(
        string='Total Intake Consumptions of Company 03',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_03 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 03',
        default=0.0,
        digits=(32, 4))


class WuaSumIntakeconsumptionInvoicing(models.Model):
    _name = 'wua.sum.intakeconsumption.invoicing'
    _auto = False

    balance_id = fields.Many2one(
        string='Balance',
        comodel_name='wua.intakeconsumption.balance',
        index=True,
        ondelete='cascade')

    year = fields.Integer(
        string='Year')

    month = fields.Integer(
        string='Month')

    month_name = fields.Char(
        string='Month',
        size=15,
        compute='_compute_month_name',
        store=False)

    month_year_name = fields.Char(
        string='Month/Year',
        size=18,
        compute='_compute_month_year_name',
        store=False)

    sum_intakeconsumption_company_01 = fields.Float(
        string='Total Intake Consumptions of Company 01',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_01 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 01',
        default=0.0,
        digits=(32, 4))

    difference_intakeconsumption_invoicing_company_01 = fields.Float(
        string='Difference Between the real Intake Consumption and the Intake'
        'Consumption Invoiced of Company 01',
        default=0.0,
        digits=(32, 4))

    sum_intakeconsumption_company_02 = fields.Float(
        string='Total Intake Consumptions of Company 02',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_02 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 02',
        default=0.0,
        digits=(32, 4))

    difference_intakeconsumption_invoicing_company_02 = fields.Float(
        string='Difference Between the real Intake Consumption and the Intake'
        'Consumption Invoiced of Company 02',
        default=0.0,
        digits=(32, 4))

    sum_intakeconsumption_company_03 = fields.Float(
        string='Total Intake Consumptions of Company 03',
        default=0.0,
        digits=(32, 4))

    sum_invoicing_company_03 = fields.Float(
        string='Total Intake Consumptions Invoiced of Company 03',
        default=0.0,
        digits=(32, 4))

    difference_intakeconsumption_invoicing_company_03 = fields.Float(
        string='Difference Between the real Intake Consumption and the Intake'
        'Consumption Invoiced of Company 03',
        default=0.0,
        digits=(32, 4))

    @api.multi
    def _compute_month_name(self):
        for record in self:
            month_name = ''
            if (record.month):
                month_name = \
                    fields.Datetime.from_string(
                        '1996-' + str(record.month) + '-1 0:0:0').strftime(
                        '%B').capitalize()
            record.month_name = month_name

    @api.multi
    def _compute_month_year_name(self):
        for record in self:
            month_year_name = ''
            if (record.month and record.year):
                month_year_name = \
                    fields.Datetime.from_string(
                        '1996-' + str(record.month) + '-1 0:0:0').strftime(
                        '%B').capitalize() + '/' + str(record.year)[-2:]
            record.month_year_name = month_year_name

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaSumIntakeconsumptionInvoicing, self).\
            fields_view_get(view_id=view_id,
                            view_type=view_type,
                            toolbar=toolbar,
                            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            company_01_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_01_abv')
            company_02_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_02_abv')
            company_03_abv = self.env['ir.values'].get_default(
                'wua.configuration', 'company_03_abv')
            if company_01_abv:
                for node in doc.xpath(
                        "//field[@name='sum_intakeconsumption_company_01']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_01_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='sum_invoicing_company_01']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_01_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='difference_intakeconsumption_invoicing"
                        "_company_01']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_01_abv.decode('utf-8'))
            if company_02_abv:
                for node in doc.xpath(
                        "//field[@name='sum_intakeconsumption_company_02']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_02_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='sum_invoicing_company_02']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_02_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='difference_intakeconsumption_invoicing"
                        "_company_02']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_02_abv.decode('utf-8'))
            if company_03_abv:
                for node in doc.xpath(
                        "//field[@name='sum_intakeconsumption_company_03']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_03_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='sum_invoicing_company_03']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_03_abv.decode('utf-8'))
                for node in doc.xpath(
                        "//field[@name='difference_intakeconsumption_invoicing"
                        "_company_03']"):
                    node.set('string',
                             node.get('string') + ' ' +
                             company_03_abv.decode('utf-8'))
            res['arch'] = etree.tostring(doc)
        return res

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_sum_intakeconsumption_invoicing')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_intakeconsumption_invoicing AS (
            SELECT row_number() OVER() AS id, a.* FROM (
            SELECT wibm1.balance_id, wibm1.month, wibm1.year,
            COALESCE(consumption.sum_intakeconsumption_company_01, 0.0000) AS
                sum_intakeconsumption_company_01,
            COALESCE(consumption.sum_intakeconsumption_company_02, 0.0000) AS
                sum_intakeconsumption_company_02,
            COALESCE(consumption.sum_intakeconsumption_company_03, 0.0000) AS
                sum_intakeconsumption_company_03,
            COALESCE(invoicing.sum_invoicing_company_01, 0.0000) AS
                sum_invoicing_company_01,
            COALESCE(invoicing.sum_invoicing_company_02, 0.0000) AS
                sum_invoicing_company_02,
            COALESCE(invoicing.sum_invoicing_company_03, 0.0000) AS
                sum_invoicing_company_03,
            COALESCE(consumption.sum_intakeconsumption_company_01, 0.0000) -
            COALESCE(invoicing.sum_invoicing_company_01, 0.0000) AS
                difference_intakeconsumption_invoicing_company_01,
            COALESCE(consumption.sum_intakeconsumption_company_02, 0.0000) -
            COALESCE(invoicing.sum_invoicing_company_02, 0.0000) AS
                difference_intakeconsumption_invoicing_company_02,
            COALESCE(consumption.sum_intakeconsumption_company_03, 0.0000) -
            COALESCE(invoicing.sum_invoicing_company_03, 0.0000) AS
                difference_intakeconsumption_invoicing_company_03
            FROM wua_intakeconsumption_balance_month wibm1
            INNER JOIN wua_intakeconsumption_balance wib1 ON
                wibm1.balance_id = wib1.id
            LEFT JOIN
            (SELECT
                COALESCE(c2.year, c1.year, c3.year) as year,
                COALESCE(c2.month, c1.month, c3.month) as month,
                c1.sum_intakeconsumption_company_01,
                c2.sum_intakeconsumption_company_02,
                c3.sum_intakeconsumption_company_03
                FROM
                (select year, month, volume_total AS
                sum_intakeconsumption_company_01
                FROM wua_sum_intakeconsumption where company =
                    'company_01') c1
                FULL OUTER JOIN
                (select year, month, volume_total AS
                sum_intakeconsumption_company_02
                FROM wua_sum_intakeconsumption where company =
                    'company_02') c2
                ON c1.year = c2.year AND c1.month = c2.month
                FULL OUTER JOIN
                (select year, month, volume_total as
                sum_intakeconsumption_company_03
                FROM wua_sum_intakeconsumption where company =
                    'company_03') c3
                ON c3.year = (CASE WHEN (c1.year IS NOT NULL) THEN c1.year ELSE
                c2.year END) AND c3.month = (CASE WHEN (c1.month IS NOT NULL)
                THEN c1.month ELSE c2.month END)
            ) consumption
            ON
            wibm1.year = consumption.year
            AND wibm1.month = consumption.month
            LEFT JOIN
            (SELECT
                COALESCE(c2.year, c1.year, c3.year) as year,
                COALESCE(c2.month, c1.month, c3.month) as month,
                c1.sum_invoicing_company_01,
                c2.sum_invoicing_company_02,
                c3.sum_invoicing_company_03
                FROM
                (SELECT year, month, total_quantity AS
                sum_invoicing_company_01
                FROM wua_sum_invoicing where company = 'company_01') c1
                FULL OUTER JOIN
                (select year, month, total_quantity as
                sum_invoicing_company_02
                from wua_sum_invoicing where company = 'company_02') c2
                ON c1.year = c2.year AND c1.month = c2.month
                FULL OUTER JOIN
                (select year, month, total_quantity as
                sum_invoicing_company_03
                FROM
                wua_sum_invoicing where company = 'company_03') c3
                ON c3.year = (CASE WHEN (c1.year IS NOT NULL) THEN c1.year ELSE
                c2.year END) AND c3.month = (CASE WHEN (c1.month IS NOT NULL)
                THEN c1.month ELSE c2.month END)
            ) invoicing
            ON
            wibm1.month = invoicing.month AND
            wibm1.year = invoicing.year
            ORDER BY wibm1.year, wibm1.month ASC
            ) a )
            """)
