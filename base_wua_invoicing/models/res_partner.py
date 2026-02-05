# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_overdue = fields.Monetary(
        compute='_compute_credit_overdue',
        string='Overdue Receivable',
        search='_search_credit_overdue',
        help="Overdue amount this customer owes you.")

    @api.multi
    def _compute_credit_overdue(self):
        tables, where_clause, where_params = \
            self.env['account.move.line']._query_get()
        tables = tables  # avoid warning
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self.sudo()._cr.execute("""SELECT account_move_line.partner_id,
                            act.type,
                            SUM(account_move_line.amount_residual)
                            FROM account_move_line
                            LEFT JOIN account_account a
                            ON (account_move_line.account_id=a.id)
                            LEFT JOIN account_account_type act
                            ON (a.user_type_id=act.id)
                            WHERE act.type IN ('receivable')
                            AND account_move_line.partner_id IN %s
                            AND account_move_line.reconciled IS FALSE
                            AND current_date >
                            account_move_line.date_maturity
                            """ + where_clause + """
                            GROUP BY account_move_line.partner_id, act.type
                            """, where_params)
        for pid, act_type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if act_type == 'receivable':
                partner.credit_overdue = val

    def _search_credit_overdue(self, operator, value):
        tables, where_clause, where_params = self.env['account.move.line'].\
            _query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause
        query = """
            SELECT account_move_line.partner_id
            FROM account_move_line
            LEFT JOIN account_account a ON
                (account_move_line.account_id = a.id)
            LEFT JOIN account_account_type act ON (a.user_type_id = act.id)
            WHERE act.type = 'receivable'
              AND account_move_line.reconciled IS FALSE
              AND current_date > account_move_line.date_maturity
            GROUP BY account_move_line.partner_id
            HAVING SUM(account_move_line.amount_residual) {operator} %s
        """.format(operator=operator)
        self.env.cr.execute(query + where_clause, [value] + where_params)
        partner_ids = [row[0] for row in self.env.cr.fetchall()]
        return [('id', 'in', partner_ids)]

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_tree_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_partner_view_tree').id
        search_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_partner_view_search')
        id_pivot_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_partner_view_pivot').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Invoice Lines'),
            'res_model': 'account.invoice.line',
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'views': [(id_tree_view, 'tree'), (id_pivot_view, 'pivot')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {
                'group_by': 'categ_id',
            },
            }
        return act_window

    @api.multi
    def action_see_invoices(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_tree_view = self.env.ref(
            'base_wua_invoicing.invoice_tree').id
        id_form_view = self.env.ref(
            'base_wua_invoicing.invoice_form').id
        search_view = self.env.ref(
            'base_wua_invoicing.view_account_invoice_filter')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def action_see_overdue_credits(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id),
                     ('account_id.internal_type', 'in', ['receivable']),
                     ('days_overdue', '>', 0)]
        id_tree_view = self.env.ref(
            'account_due_list.view_payments_tree').id
        search_view = self.env.ref(
            'account_due_list.view_payments_filter')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Due List'),
            'res_model': 'account.move.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def archive_partner(self):
        """Archive partners with wizard confirmation for suppliers"""
        partners_to_archive = self.filtered(lambda p: p.active)

        if partners_to_archive:
            supplier_partners = partners_to_archive.filtered(lambda p: p.supplier)
            if supplier_partners:
                # Crear el wizard con todos los partners seleccionados
                # El wizard mostrará solo los proveedores en el mensaje
                wizard = self.env['res.partner.archive.wizard'].create({
                    'partner_ids': [(6, 0, self.ids)],
                })
                return {
                    'name': _('Archive Supplier Warning'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner.archive.wizard',
                    'res_id': wizard.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                }

        # Si no hay proveedores, archivar directamente
        self.write({'active': False})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def toggle_active(self):
        """Override toggle_active to show confirmation wizard for suppliers"""
        # Solo interceptar cuando se va a archivar (partners activos)
        partners_to_archive = self.filtered(lambda p: p.active)

        if partners_to_archive and not self._context.get('confirmed_archive'):
            supplier_partners = partners_to_archive.filtered(lambda p: p.supplier)
            if supplier_partners:
                # Mostrar wizard de confirmación
                wizard = self.env['res.partner.archive.wizard'].create({
                    'partner_ids': [(6, 0, self.ids)],
                })
                return {
                    'name': _('Archive Supplier Warning'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner.archive.wizard',
                    'res_id': wizard.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                }

        # Si no son proveedores o viene confirmado, ejecutar normal
        return super(ResPartner, self).toggle_active()


