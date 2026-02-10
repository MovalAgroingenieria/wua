# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import operator as op


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
        # Query to get partners with overdue credit (only non-zero amounts)
        query = """
            SELECT account_move_line.partner_id,
                   SUM(account_move_line.amount_residual) as total
            FROM account_move_line
            LEFT JOIN account_account a ON
                (account_move_line.account_id = a.id)
            LEFT JOIN account_account_type act ON (a.user_type_id = act.id)
            WHERE act.type = 'receivable'
              AND account_move_line.reconciled IS FALSE
              AND current_date > account_move_line.date_maturity
              AND account_move_line.partner_id IS NOT NULL
              {where_clause}
            GROUP BY account_move_line.partner_id
            HAVING SUM(account_move_line.amount_residual) != 0
        """.format(where_clause=where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        # Build dict of partner_id -> overdue amount (only non-zero)
        partner_overdue = {row[0]: row[1] for row in results}
        partners_with_nonzero_overdue = list(partner_overdue.keys())
        # Handle different operators
        if operator == '=' and value == 0:
            # Partners with credit_overdue = 0 are those NOT in the
            # non-zero list
            if not partners_with_nonzero_overdue:
                # All partners have 0 overdue
                return [(1, '=', 1)]
            return [('id', 'not in', partners_with_nonzero_overdue)]
        elif operator == '!=' and value == 0:
            # Partners with credit_overdue != 0 are those with sum != 0
            if not partners_with_nonzero_overdue:
                return [(0, '=', 1)]  # No results
            return [('id', 'in', partners_with_nonzero_overdue)]
        elif operator in ('>', '>=', '<', '<=', '=', '!='):
            # Apply operator to the amounts
            ops = {
                '>': op.gt, '>=': op.ge, '<': op.lt,
                '<=': op.le, '=': op.eq, '!=': op.ne,
            }
            matching_partners = [pid for pid, amt in partner_overdue.items()
                                 if ops[operator](amt, value)]
            # For < and <= with positive value, include partners without
            # overdue (they have 0)
            if operator in ('<', '<=') and value > 0:
                if not partners_with_nonzero_overdue:
                    return [(1, '=', 1)]  # All partners match
                return ['|',
                        ('id', 'not in', partners_with_nonzero_overdue),
                        ('id', 'in', matching_partners)]
            if not matching_partners:
                return [(0, '=', 1)]  # No results
            return [('id', 'in', matching_partners)]
        else:
            return [(0, '=', 1)]  # No results

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
            supplier_partners = partners_to_archive.filtered(
                lambda p: p.supplier)
            if supplier_partners:
                # Create wizard with all selected partners
                # The wizard will show only suppliers in the message
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

        # If there are no suppliers, archive directly
        self.write({'active': False})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def toggle_active(self):
        """Override toggle_active to show confirmation wizard for suppliers"""
        # Only intercept when archiving (active partners)
        partners_to_archive = self.filtered(lambda p: p.active)

        if partners_to_archive and not self._context.get('confirmed_archive'):
            supplier_partners = partners_to_archive.filtered(
                lambda p: p.supplier)
            if supplier_partners:
                # Show confirmation wizard
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
        # If not suppliers or already confirmed, execute normally
        return super(ResPartner, self).toggle_active()
