# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class _FakeNS(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeLineHydricmovement(object):
    """Mimics a `wua.invoiceset.line.hydricmovement` record.

    Only exposes the attributes used by `select_invoice_items_other_types`
    in `base_wua_invoicing_hydricmovement` and the threshold logic.
    """

    def __init__(self, hydricmovement_id, waterconnection_id, volume,
                 hm_type='pres_consumption', selected=True,
                 partner_active=True):
        self.selected = selected
        wc_ns = _FakeNS(id=waterconnection_id) if waterconnection_id \
            else _FakeNS(id=False)
        presconsumption = _FakeNS(
            id=hydricmovement_id,
            waterconnection_id=wc_ns,
        ) if hm_type == 'pres_consumption' else _FakeNS(
            id=False, waterconnection_id=_FakeNS(id=False))
        self.hydricmovement_id = _FakeNS(
            id=hydricmovement_id,
            type=hm_type,
            volume=volume,
            presconsumption_id=presconsumption,
            partner_id=_FakeNS(active=partner_active),
            invoiceset_id=_FakeNS(id=1),
            invoiced_hydricmovement=True,
        )


class _FakeRecordset(object):

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
        self.line_hydricmovement_ids = _FakeRecordset(lines)
        self.min_consumption_threshold_per_wc = threshold_override


class TestMinConsumptionThresholdHmov(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestMinConsumptionThresholdHmov, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']
        cls.IrValues = cls.env['ir.values'].sudo()

    def setUp(self):
        super(TestMinConsumptionThresholdHmov, self).setUp()
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
    # Filter behavior on categ 14 (hydric movements of type
    # pres_consumption)
    # ---------------------------------------------------------------
    def test_select_returns_all_when_threshold_disabled(self):
        self._set_config(apply_flag=False, global_threshold=100.0)
        lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=10, volume=5.0),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=20, volume=200.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(14, ils)
        self.assertEqual(sorted(result), [1, 2])
        self.assertTrue(all(l.selected for l in lines))

    def test_select_filters_below_threshold_per_wc(self):
        self._set_config(apply_flag=True, global_threshold=100.0)
        lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=10, volume=10.0),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=10, volume=20.0),
            _FakeLineHydricmovement(
                hydricmovement_id=3, waterconnection_id=20, volume=120.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(14, ils)
        self.assertEqual(sorted(result), [3])
        excluded = [l for l in lines if l.hydricmovement_id.id in (1, 2)]
        self.assertTrue(all(l.selected is False for l in excluded))

    def test_threshold_does_not_affect_non_pres_consumption_types(self):
        """Hydric movements of other types must not be filtered or grouped
        by waterconnection."""
        self._set_config(apply_flag=True, global_threshold=100.0)
        lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=False, volume=5.0,
                hm_type='granted_cession'),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=10, volume=10.0,
                hm_type='pres_consumption'),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(14, ils)
        # The pres_consumption line is excluded (10<100); the
        # granted_cession one is kept untouched regardless of threshold.
        self.assertEqual(sorted(result), [1])
        self.assertTrue(lines[0].selected)
        self.assertFalse(lines[1].selected)

    def test_archived_partner_movements_are_skipped_before_threshold(self):
        """Movements with archived partner are excluded by the existing
        filter even if they would help reach the threshold."""
        self._set_config(apply_flag=True, global_threshold=100.0)
        lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=10, volume=80.0,
                partner_active=False),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=10, volume=30.0),
        ]
        ils = _FakeInvoicesetLine(lines)
        result = self.Invoiceset.select_invoice_items_other_types(14, ils)
        # Only the active-partner one is considered; total is 30 < 100.
        self.assertEqual(result, [])

    # ---------------------------------------------------------------
    # Two-billing scenario.
    # ---------------------------------------------------------------
    def test_carryover_invoiced_in_next_invoiceset(self):
        self._set_config(apply_flag=True, global_threshold=100.0)
        first_lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=10, volume=10.0),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=10, volume=20.0),
        ]
        first_ils = _FakeInvoicesetLine(first_lines)
        first_result = self.Invoiceset.select_invoice_items_other_types(
            14, first_ils)
        self.assertEqual(first_result, [])
        # Simulate after_calculate_invoiceset cleanup for unselected: the
        # related wua.hydricmovement is left with
        # `invoiced_hydricmovement=False` and `invoiceset_id=None`, so it
        # will reappear in the next invoiceset.
        carried_over = []
        for fl in first_lines:
            if fl.selected is False:
                hm = fl.hydricmovement_id
                hm.invoiced_hydricmovement = False
                hm.invoiceset_id = _FakeNS(id=False)
                carried_over.append(hm)
        self.assertEqual(len(carried_over), 2)
        for hm in carried_over:
            self.assertFalse(hm.invoiced_hydricmovement)
            self.assertFalse(hm.invoiceset_id.id)

        # Next invoiceset: same WC accumulates a new movement that pushes
        # the total over the threshold.
        second_lines = [
            _FakeLineHydricmovement(
                hydricmovement_id=1, waterconnection_id=10, volume=10.0),
            _FakeLineHydricmovement(
                hydricmovement_id=2, waterconnection_id=10, volume=20.0),
            _FakeLineHydricmovement(
                hydricmovement_id=3, waterconnection_id=10, volume=80.0),
        ]
        second_ils = _FakeInvoicesetLine(second_lines)
        second_result = self.Invoiceset.select_invoice_items_other_types(
            14, second_ils)
        self.assertEqual(sorted(second_result), [1, 2, 3])
        self.assertTrue(all(l.selected for l in second_lines))
