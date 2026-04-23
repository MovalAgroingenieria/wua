# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class _FakeNS(object):
    """Tiny namespace whose attributes can be both read and reassigned."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeLinePresconsumption(object):
    """Mimics a `wua.invoiceset.line.presconsumption` record for filtering.

    Only exposes the attributes used by
    `select_invoice_items_other_types` and the threshold logic.
    """

    def __init__(self, presconsumption_id, waterconnection_id,
                 volume_real, selected=True):
        self.selected = selected
        self.waterconnection_id = _FakeNS(id=waterconnection_id)
        self.presconsumption_id = _FakeNS(
            id=presconsumption_id,
            volume_real=volume_real,
            waterconnection_id=self.waterconnection_id,
            invoiceset_id=_FakeNS(id=1),
            invoiced_consumption=True,
        )


class _FakeRecordset(object):
    """Recordset-like wrapper around a list of `_FakeLinePresconsumption`."""

    def __init__(self, records):
        self._records = list(records)

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)

    def __bool__(self):
        return bool(self._records)

    __nonzero__ = __bool__  # Py2

    def __sub__(self, other):
        other_ids = set(id(r) for r in other._records)
        return _FakeRecordset(
            [r for r in self._records if id(r) not in other_ids])

    def filtered(self, fn):
        return _FakeRecordset([r for r in self._records if fn(r)])

    def write(self, vals):
        for r in self._records:
            for k, v in vals.items():
                setattr(r, k, v)
        return True


class _FakeInvoicesetLine(object):

    def __init__(self, lines, threshold_override=0.0):
        self.line_presconsumption_ids = _FakeRecordset(lines)
        self.min_consumption_threshold_per_wc = threshold_override


class TestMinConsumptionThreshold(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestMinConsumptionThreshold, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']
        cls.IrValues = cls.env['ir.values'].sudo()
        # Snapshot original config values so each test starts from a known
        # state.
        cls._original_apply = cls.IrValues.get_default(
            'wua.invoicing.configuration',
            'apply_min_consumption_threshold_per_wc')
        cls._original_global = cls.IrValues.get_default(
            'wua.invoicing.configuration',
            'min_consumption_threshold_per_wc')

    def setUp(self):
        super(TestMinConsumptionThreshold, self).setUp()
        # SavepointCase rolls back DB changes between tests, including
        # ir.values, so we just reset to a clean disabled state.
        self._set_config(apply_flag=False, global_threshold=0.0)

    def _set_config(self, apply_flag, global_threshold):
        self.IrValues.set_default(
            'wua.invoicing.configuration',
            'apply_min_consumption_threshold_per_wc',
            apply_flag)
        self.IrValues.set_default(
            'wua.invoicing.configuration',
            'min_consumption_threshold_per_wc',
            global_threshold)

    # ---------------------------------------------------------------
    # _get_min_consumption_threshold_per_wc
    # ---------------------------------------------------------------
    def test_threshold_zero_when_flag_disabled(self):
        self._set_config(apply_flag=False, global_threshold=100.0)
        line = _FakeInvoicesetLine([], threshold_override=50.0)
        self.assertEqual(
            self.Invoiceset._get_min_consumption_threshold_per_wc(line), 0.0)

    def test_threshold_uses_line_override_when_flag_enabled(self):
        self._set_config(apply_flag=True, global_threshold=10.0)
        line = _FakeInvoicesetLine([], threshold_override=50.0)
        self.assertEqual(
            self.Invoiceset._get_min_consumption_threshold_per_wc(line), 50.0)

    def test_threshold_falls_back_to_global_when_line_zero(self):
        self._set_config(apply_flag=True, global_threshold=10.0)
        line = _FakeInvoicesetLine([], threshold_override=0.0)
        self.assertEqual(
            self.Invoiceset._get_min_consumption_threshold_per_wc(line), 10.0)

    def test_threshold_zero_when_flag_enabled_but_no_value(self):
        self._set_config(apply_flag=True, global_threshold=0.0)
        line = _FakeInvoicesetLine([], threshold_override=0.0)
        self.assertEqual(
            self.Invoiceset._get_min_consumption_threshold_per_wc(line), 0.0)

    # ---------------------------------------------------------------
    # select_invoice_items_other_types: filter behavior
    # ---------------------------------------------------------------
    def test_select_returns_all_when_threshold_disabled(self):
        self._set_config(apply_flag=False, global_threshold=100.0)
        lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=10, volume_real=5.0),
            _FakeLinePresconsumption(
                presconsumption_id=2, waterconnection_id=20, volume_real=200.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(7, ils)
        self.assertEqual(sorted(result), [1, 2])
        # Nothing was unselected.
        self.assertTrue(all(l.selected for l in lines))

    def test_select_filters_below_threshold_per_wc(self):
        """WC 10 sums 30 (<100) → excluded; WC 20 sums 250 (>=100) → kept."""
        self._set_config(apply_flag=True, global_threshold=100.0)
        lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=10, volume_real=10.0),
            _FakeLinePresconsumption(
                presconsumption_id=2, waterconnection_id=10, volume_real=20.0),
            _FakeLinePresconsumption(
                presconsumption_id=3, waterconnection_id=20, volume_real=120.0),
            _FakeLinePresconsumption(
                presconsumption_id=4, waterconnection_id=20, volume_real=130.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(7, ils)
        self.assertEqual(sorted(result), [3, 4])
        # Excluded ones got `selected=False` (so that
        # after_calculate_invoiceset later releases them as not invoiced).
        excluded = [l for l in lines if l.presconsumption_id.id in (1, 2)]
        self.assertTrue(all(l.selected is False for l in excluded))
        kept = [l for l in lines if l.presconsumption_id.id in (3, 4)]
        self.assertTrue(all(l.selected for l in kept))

    def test_select_keeps_wc_exactly_at_threshold(self):
        """Threshold check is strict `<`: a WC reaching exactly the
        threshold is kept."""
        self._set_config(apply_flag=True, global_threshold=100.0)
        lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=10, volume_real=60.0),
            _FakeLinePresconsumption(
                presconsumption_id=2, waterconnection_id=10, volume_real=40.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(7, ils)
        self.assertEqual(sorted(result), [1, 2])

    def test_line_override_wins_over_global(self):
        """Line threshold (200) excludes WC 20 even though global (50) would
        keep it."""
        self._set_config(apply_flag=True, global_threshold=50.0)
        lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=20, volume_real=120.0),
        ]
        ils = _FakeInvoicesetLine(lines, threshold_override=200.0)
        result = self.Invoiceset.select_invoice_items_other_types(7, ils)
        self.assertEqual(result, [])
        self.assertFalse(lines[0].selected)

    # ---------------------------------------------------------------
    # Two-billing scenario: leftovers from first batch are billable
    # in the next one if the new total reaches the threshold.
    # ---------------------------------------------------------------
    def test_carryover_invoiced_in_next_invoiceset(self):
        """First invoice-set: WC 10 has 30 m³ → below threshold (100), gets
        excluded. After `after_calculate_invoiceset` simulation those rows
        are deleted and the original presconsumptions get
        `invoiced_consumption=False` and `invoiceset_id=None` (released).

        Second invoice-set: those same presconsumptions are re-picked
        together with a new one of 80 m³; total for WC 10 is now 110 m³
        (>=100), so all three (the two carried over and the new one) are
        invoiced.
        """
        self._set_config(apply_flag=True, global_threshold=100.0)

        # ---- First invoice set ----
        first_lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=10, volume_real=10.0),
            _FakeLinePresconsumption(
                presconsumption_id=2, waterconnection_id=10, volume_real=20.0),
        ]
        first_ils = _FakeInvoicesetLine(first_lines)
        first_result = self.Invoiceset.select_invoice_items_other_types(
            7, first_ils)
        self.assertEqual(first_result, [],
                         "Below-threshold WC must not be invoiced.")
        # Simulate `after_calculate_invoiceset` cleanup: the unselected
        # line_presconsumption rows would be unlinked and the related
        # wua.presconsumption records reset.
        carried_over = []
        for fl in first_lines:
            if fl.selected is False:
                pc = fl.presconsumption_id
                pc.invoiced_consumption = False
                pc.invoiceset_id = _FakeNS(id=False)
                carried_over.append(pc)
        self.assertEqual(len(carried_over), 2)
        for pc in carried_over:
            self.assertFalse(pc.invoiced_consumption)
            self.assertFalse(pc.invoiceset_id.id)

        # ---- Second invoice set: same two presconsumptions show up
        # again (because they were released) plus a new 80 m³ on WC 10. ----
        second_lines = [
            _FakeLinePresconsumption(
                presconsumption_id=1, waterconnection_id=10, volume_real=10.0),
            _FakeLinePresconsumption(
                presconsumption_id=2, waterconnection_id=10, volume_real=20.0),
            _FakeLinePresconsumption(
                presconsumption_id=3, waterconnection_id=10, volume_real=80.0),
        ]
        second_ils = _FakeInvoicesetLine(second_lines)
        second_result = self.Invoiceset.select_invoice_items_other_types(
            7, second_ils)
        # WC 10 now sums 110 (>=100): everything (incl. carry-overs) is
        # invoiced.
        self.assertEqual(sorted(second_result), [1, 2, 3])
        self.assertTrue(all(l.selected for l in second_lines))
