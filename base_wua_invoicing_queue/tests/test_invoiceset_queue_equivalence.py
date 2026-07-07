# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestInvoicesetQueueEquivalence(common.TransactionCase):
    """The parallel (queue) flow must produce EXACTLY the same result as the
    classic sequential calculate_invoiceset()."""

    def setUp(self):
        super(TestInvoicesetQueueEquivalence, self).setUp()
        self.invoiceset_model = self.env['wua.invoiceset']

    def _find_source_invoiceset(self):
        # Use a configured, not-yet-generated invoice set as fixture. If none
        # exists in this database, the test is skipped (no synthetic data is
        # invented here to avoid false negatives).
        candidates = self.invoiceset_model.search(
            [('state', '=', 'draft'),
             ('configured_invoiceset', '=', True)])
        for candidate in candidates:
            if candidate.line_ids:
                return candidate
        return self.invoiceset_model.browse()

    def _run_classic(self, source):
        classic = source.copy()
        classic.calculate_invoiceset()
        return classic

    def _run_parallel(self, source):
        parallel = source.copy()
        # Run the queue pipeline synchronously (no worker in tests): build the
        # plan and materialize it directly, bypassing with_delay().
        plan = parallel._create_plan()
        parallel.with_context(
            queue_background_calculation=True)._build_plan(plan)
        parallel._materialize_plan(plan)
        return parallel

    def _assert_equivalent(self, classic, parallel):
        self.assertEqual(
            classic.state, 'generated',
            'Classic calculation did not generate the invoice set.')
        self.assertEqual(
            parallel.state, 'generated',
            'Parallel calculation did not generate the invoice set.')
        self.assertEqual(
            classic.number_of_invoices, parallel.number_of_invoices,
            'Number of invoices differs between classic and parallel.')
        self.assertAlmostEqual(
            classic.amount_untaxed, parallel.amount_untaxed, 2,
            'amount_untaxed differs between classic and parallel.')
        self.assertAlmostEqual(
            classic.amount_tax, parallel.amount_tax, 2,
            'amount_tax differs between classic and parallel.')
        self.assertAlmostEqual(
            classic.amount_total, parallel.amount_total, 2,
            'amount_total differs between classic and parallel.')

    def test_equivalence_classic_vs_parallel(self):
        source = self._find_source_invoiceset()
        if not source:
            self.skipTest(
                'No configured draft invoice set with lines available '
                'as a fixture in this database.')
        classic = self._run_classic(source)
        parallel = self._run_parallel(source)
        self._assert_equivalent(classic, parallel)

    def test_materialize_is_idempotent(self):
        source = self._find_source_invoiceset()
        if not source:
            self.skipTest(
                'No configured draft invoice set with lines available '
                'as a fixture in this database.')
        parallel = source.copy()
        plan = parallel._create_plan()
        parallel.with_context(
            queue_background_calculation=True)._build_plan(plan)
        parallel._materialize_plan(plan)
        invoices_after_first = self.env['account.invoice'].search_count(
            [('invoiceset_id', '=', parallel.id)])
        # Re-running the materialization must NOT create duplicate invoices,
        # because every plan line is already in state 'done'.
        parallel._materialize_plan(plan)
        invoices_after_second = self.env['account.invoice'].search_count(
            [('invoiceset_id', '=', parallel.id)])
        self.assertEqual(
            invoices_after_first, invoices_after_second,
            'Re-materializing created duplicate invoices (not idempotent).')
