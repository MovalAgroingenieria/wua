# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, tools, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    agriculturalseason_month_ids = fields.One2many(
        string='Agriculturalseason Months',
        comodel_name='wua.agriculturalseason.month',
        inverse_name='agriculturalseason_id',)

    @api.multi
    def action_see_sum_intakeconsumption_invoicing(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_tree_view = self.env.ref('wua_cgrabaran.'
                                    'wua_sum_intakeconsumption_invoicing_view'
                                    '_tree').id
        search_view = self.env.ref('wua_cgrabaran.'
                                   'wua_sum_intakeconsumption_invoicing_view'
                                   '_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumption balance'),
            'res_model': 'wua.sum.intakeconsumption.invoicing',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.model
    def create(self, vals):
        agriculturalseason_created =  \
            super(WuaAgriculturalseason, self).create(vals)
        if agriculturalseason_created:
            print agriculturalseason_created.id
            for month in range(1, 13):
                self.env['wua.agriculturalseason.month'].create({
                    'agriculturalseason_id': agriculturalseason_created.id,
                    'month': month
                    })
        return agriculturalseason_created

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'wua_sum_intakeconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_intakeconsumption AS (
            SELECT row_number() OVER() AS id, a.* FROM (SELECT
            wi1.company_id AS company_id, iv1.name AS company,
            extract (month FROM ((wic1.reading_initial_time AT TIME ZONE 'UTC')
            AT TIME ZONE 'Europe/Madrid')) AS month,
            extract(year from ((wic1.reading_initial_time AT TIME ZONE 'UTC')
            AT TIME ZONE 'Europe/Madrid')) AS year, sum(wic1.volume_real) AS
            volume_total,  wic1.agriculturalseason_id AS
            agriculturalseason_id FROM wua_intakeconsumption wic1
            LEFT JOIN wua_intake wi1 ON wi1.id = wic1.intake_id LEFT JOIN
            ir_values iv1 ON wi1.company_id = (CAST(substring(iv1.value from
            \'\\d\') AS INTEGER)) where iv1.model = 'wua.configuration' and
            (iv1.name = 'company_01' OR iv1.name = 'company_02' OR iv1.name =
            'company_03') AND validated AND wi1.company_id IS NOT NULL GROUP BY
            month, year, agriculturalseason_id, iv1.name, wi1.company_id
            ORDER BY agriculturalseason_id, iv1.name, year, month)
             a)
            """)
        tools.drop_view_if_exists(self.env.cr, 'wua_sum_invoicing')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_invoicing AS (
            SELECT row_number() OVER() AS id, a.* FROM (SELECT
            a1.company_id, iv1.name as company, extract (year FROM
            ((a1.date_invoice AT TIME ZONE 'UTC' ) AT TIME ZONE
            'Europe/Madrid')) AS year, extract (month FROM ((a1.date_invoice AT
            TIME ZONE 'UTC' ) AT TIME ZONE 'Europe/Madrid')) AS month,
            SUM(a1.quantity) AS total_quantity FROM
            account_invoice_line a1 INNER JOIN
            product_category p1 ON a1.categ_id = p1.id INNER JOIN ir_values iv1
            ON a1.company_id = (CAST(substring(iv1.value from
            \'\\d\') AS INTEGER)) WHERE iv1.model = 'wua.configuration' and
            (iv1.name = 'company_01' OR iv1.name = 'company_02' OR iv1.name =
            'company_03') AND (p1.productcategory_code = 7 OR
            p1.productcategory_code = 11) GROUP BY a1.company_id, year, month,
            iv1.name ORDER BY iv1.name, year, month) a)
            """)
        super(WuaAgriculturalseason, self).init()


class WuaAgriculturalseasonMonth(models.Model):

    _name = 'wua.agriculturalseason.month'
    _description = 'Entity (agriculturalseason)'

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='cascade',
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

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='cascade')

    month = fields.Integer(
        string='Month')

    month_name = fields.Char(
        string='Month',
        size=15,
        compute='_compute_month_name')

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

    @api.depends('month')
    def _compute_month_name(self):
        for record in self:
            if (record.month):
                record.month_name = \
                    fields.Datetime.from_string(
                        '1996-' + str(record.month) + '-1 0:0:0').strftime(
                        '%B').capitalize()

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
            res['arch'] = etree.tostring(doc)
        return res

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_sum_intakeconsumption_invoicing')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_sum_intakeconsumption_invoicing AS (
            SELECT row_number() OVER() AS id, a.* FROM (
            SELECT wam1.agriculturalseason_id, wam1.month,
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
                sum_invoicing_company_03
            FROM wua_agriculturalseason_month wam1
            INNER JOIN wua_agriculturalseason wa1 ON
                wam1.agriculturalseason_id = wa1.id
            LEFT JOIN
            (SELECT
                COALESCE(c2.year, c1.year, c3.year) as year,
                COALESCE(c2.month, c1.month, c3.month) as month,
                COALESCE(c2.agriculturalseason_id, c1.agriculturalseason_id,
                c3.agriculturalseason_id) as agriculturalseason_id,
                c1.sum_intakeconsumption_company_01,
                c2.sum_intakeconsumption_company_02,
                c3.sum_intakeconsumption_company_03
                FROM
                (select year, month, agriculturalseason_id, volume_total AS
                sum_intakeconsumption_company_01
                FROM wua_sum_intakeconsumption where company = 'company_01') c1
                FULL OUTER JOIN
                (select year, month, agriculturalseason_id, volume_total AS
                sum_intakeconsumption_company_02
                FROM wua_sum_intakeconsumption where company = 'company_02') c2
                ON c1.year = c2.year AND c1.month = c2.month
                FULL OUTER JOIN
                (select year, month, agriculturalseason_id, volume_total as
                sum_intakeconsumption_company_03
                FROM wua_sum_intakeconsumption where company = 'company_03') c3
                ON c1.year = c3.year AND c1.month = c3.month
            ) consumption
            ON
            wam1.agriculturalseason_id = consumption.agriculturalseason_id
            AND wam1.month = consumption.month
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
                from
                wua_sum_invoicing where company = 'company_03') c3
                ON c1.year = c3.year AND c1.month = c3.month
            ) invoicing
            ON
            wam1.month = invoicing.month AND
            extract(year from (wa1.initial_date)) = invoicing.year
            ) a )
            """)
