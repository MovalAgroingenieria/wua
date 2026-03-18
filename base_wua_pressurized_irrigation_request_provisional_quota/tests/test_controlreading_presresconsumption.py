# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo.tests.common import TransactionCase


class TestControlreadingPresresconsumption(TransactionCase):
    """Tests for controlreading handling with presresconsumption
    provisional quota management.

    Covers:
    - Auto-creation of controlreadings from presresconsumptions
    - save_controlreadings: archiving prior PR readings
    - save_controlreadings: deleting/recreating posterior PR readings
    - Multiple posterior PR readings (the original bug case)
    - Different watering durations causing reading_time reordering
    - Manual (non-remote) create handling posterior/prior PR readings
    - Watermeter last_controlreading tracking correctness
    - Negative reading handling
    - Helper methods: _unlink_presresconsumption_controlreadings,
      _update_watermeter_last_reading
    """

    def setUp(self):
        super(TestControlreadingPresresconsumption, self).setUp()

        # Prevent archive_controlreadings from committing during tests
        # (archive uses raw SQL + cr.commit which would break rollback)
        self._original_commit = self.env.cr.commit
        self.env.cr.commit = lambda: None

        # Set user timezone explicitly for consistent request_time
        self.env.user.write({'tz': 'Europe/Madrid'})

        # --- Master data ---

        self.hydraulicsector = self.env['wua.hydraulicsector'].create({
            'name': 'HS-TESTCR-001',
            'description': 'Test Hydraulic Sector',
        })

        self.irrigationshed = self.env['wua.irrigationshed'].create({
            'name': 'IS-TESTCR-001',
            'hydraulicsector_id': self.hydraulicsector.id,
        })

        self.watermeter = self.env['wua.watermeter'].create({
            'name': 'WM-TESTCR-001',
            'state': 'active',
        })

        self.waterconnection = self.env['wua.waterconnection'].create({
            'name': 'WC-TESTCR-001',
            'irrigationshed_id': self.irrigationshed.id,
            'position': 1,
            'watermeter_id': self.watermeter.id,
        })

        # Initialization controlreading (required before any non-init)
        self.init_reading = self.env['wua.controlreading'].create({
            'watermeter_id': self.watermeter.id,
            'reading_time': '2026-01-01 00:00:00',
            'volume': 100.0,
            'initialization_reading': True,
        })

        # --- Presresconsumption prerequisite chain ---

        self.season = self.env['wua.agriculturalseason'].create({
            'name': 'Test Season CR 2026',
            'description': 'Test Season CR 2026',
            'initial_date': '2026-01-01',
            'end_date': '2026-12-31',
        })

        self.period = self.env['wua.preswateringperiod'].create({
            'initial_date': '2026-01-01',
            'end_date': '2026-12-31',
            'agriculturalseason_id': self.season.id,
            'state': '01_open',
        })

        self.partner = self.env['res.partner'].search([], limit=1)

        # Request with PAST date → PR reading_times before now()
        self.request_past = self.env['wua.preswateringrequest'].create({
            'preswateringperiod_id': self.period.id,
            'partner_id': self.partner.id,
            'initial_date': '2026-01-15',
        })

        # Request with FUTURE date → PR reading_times after now()
        self.request_future = self.env['wua.preswateringrequest'].create({
            'preswateringperiod_id': self.period.id,
            'partner_id': self.partner.id,
            'initial_date': '2026-12-01',
        })

        # --- Parcel chain (for particularpresconsumption tests) ---

        self.region = self.env['wua.region'].create({
            'name': 'Test Region CR',
            'code': '99',
        })
        self.region_state = self.env['wua.region.state'].create({
            'name': 'Test State CR',
            'cadastral_code': '99',
            'region_id': self.region.id,
        })
        self.county = self.env['wua.region.state.county'].create({
            'name': 'Test County CR',
            'cadastral_code': '999',
            'cadastral_state_county_code': '99999',
            'state_id': self.region_state.id,
        })

        self.parcel = self.env['wua.parcel'].create({
            'name': 'PC-TESTCR-001',
            'parcel_type': 'R',
            'county_id': self.county.id,
            'area_official': 10.0,
            'cadastral_sector': 'A',
            'cadastral_polygon': '001',
            'cadastral_parcel': '00001',
        })

        self.irrigationpoint = self.env[
            'wua.parcel.irrigationpoint'].create({
                'name': 'IP-TESTCR-001',
                'parcel_id': self.parcel.id,
                'type': 'WC',
                'waterconnection_id': self.waterconnection.id,
            })

        self.partnerlink = self.env['wua.parcel.partnerlink'].create({
            'parcel_id': self.parcel.id,
            'partner_id': self.partner.id,
            'pos': 1,
            'profile': 'O',
            'water_costs_percentage': 100.0,
            'ownership_percentage': 100.0,
            'other_costs_percentage': 100.0,
        })

        # --- Product / Superproduct chain (for quota tests) ---

        self.water_categ = self.env['product.category'].create({
            'name': 'Test Pressurized Water Cat',
            'productcategory_code': 7,
        })

        self.superproduct = self.env['wua.superproduct'].create({
            'name': 'Test Superproduct CR',
        })

        # Child product under the superproduct with pressurized category
        self.water_product_tmpl = self.env['product.template'].create({
            'name': 'Test Water Product CR',
            'categ_id': self.water_categ.id,
            'superproduct_id': self.superproduct.id,
            'type': 'service',
        })
        self.water_product = \
            self.water_product_tmpl.product_variant_ids[0]

        # Set product on waterconnection so controlpresconsumptions
        # compute product_id → superproduct_id
        self.waterconnection.write({
            'product_id': self.water_product.id,
        })

        # --- Quota chain ---

        self.season.write({'active_agriculturalseason': True})

        self.quotaperiod = self.env['wua.quotaperiod'].create({
            'initial_date': '2026-01-01',
            'end_date': '2026-12-31',
            'agriculturalseason_id': self.season.id,
        })

        self.quota = self.env['wua.quota'].create({
            'partner_id': self.partner.id,
            'superproduct_id': self.superproduct.id,
            'quotaperiod_id': self.quotaperiod.id,
            'initial_value': 1000.0,
        })
        # Force state='generated' AFTER quota creation, because
        # creating a quota triggers recomputation of quotaperiod.state
        # (depends on quota_ids) which would overwrite a prior SQL force.
        self.env.cr.execute(
            "UPDATE wua_quotaperiod SET state = 'generated' "
            "WHERE id = %s", (self.quotaperiod.id,))
        self.env['wua.quotaperiod'].invalidate_cache()
        # Force of_active_agriculturalseason (computed from season)
        self.env.cr.execute(
            "UPDATE wua_quota SET of_active_agriculturalseason = true "
            "WHERE id = %s", (self.quota.id,))
        self.env['wua.quota'].invalidate_cache()

    def tearDown(self):
        self.env.cr.commit = self._original_commit
        super(TestControlreadingPresresconsumption, self).tearDown()

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _create_presresconsumption(self, request, initial_hour=8.0,
                                   watering_duration=2.0,
                                   nominal_flow=10.0):
        """Create a presresconsumption linked to a given request."""
        return self.env['wua.presresconsumption'].create({
            'waterconnection_id': self.waterconnection.id,
            'preswateringrequest_id': request.id,
            'preswateringperiod_id': self.period.id,
            'initial_hour': initial_hour,
            'watering_duration': watering_duration,
            'nominal_flow': nominal_flow,
        })

    def _reading_payload(self, volume, watermeter=None):
        """Build a reading dict as expected by save_controlreadings."""
        wm = watermeter or self.watermeter
        return {
            'watermeter_id': wm.id,
            'volume': volume,
        }

    # ================================================================
    # 1. Presresconsumption auto-creates controlreading
    # ================================================================

    def test_01_pr_creates_controlreading(self):
        """Creating a presresconsumption auto-creates a linked
        controlreading with the correct adjustement_volume."""
        pr = self._create_presresconsumption(self.request_past)

        self.assertTrue(
            pr.controlreading_id,
            "PR should have a linked controlreading")
        cr = pr.controlreading_id
        self.assertEqual(
            cr.presresconsumption_id, pr,
            "Controlreading should link back to the PR")
        self.assertTrue(
            cr.controlpresconsumption_id,
            "Controlreading should have an auto-created "
            "controlpresconsumption")

        cp = cr.controlpresconsumption_id
        expected_vol = 2.0 * 10.0  # duration * nominal_flow
        self.assertAlmostEqual(
            cp.adjustement_volume, expected_vol, places=2,
            msg="adjustement_volume should equal watering_volume")

        # Volume should equal previous reading's volume (gross = 0)
        self.assertAlmostEqual(
            cr.volume, 100.0, places=2,
            msg="PR controlreading volume should copy previous reading")

    # ================================================================
    # 2. Multiple PRs chain volumes correctly
    # ================================================================

    def test_02_multiple_prs_chain(self):
        """Multiple PRs for the same watermeter chain correctly —
        each copies the previous reading's volume."""
        pr1 = self._create_presresconsumption(
            self.request_past, initial_hour=8.0, watering_duration=2.0)
        pr2 = self._create_presresconsumption(
            self.request_past, initial_hour=12.0, watering_duration=3.0)

        cr1, cr2 = pr1.controlreading_id, pr2.controlreading_id
        self.assertTrue(cr1 and cr2)

        self.assertAlmostEqual(cr1.volume, 100.0, places=2)
        self.assertAlmostEqual(cr2.volume, 100.0, places=2)

        self.assertAlmostEqual(
            cr1.controlpresconsumption_id.adjustement_volume,
            2.0 * 10.0, places=2)
        self.assertAlmostEqual(
            cr2.controlpresconsumption_id.adjustement_volume,
            3.0 * 10.0, places=2)

    # ================================================================
    # 3. save_controlreadings — initialization reading
    # ================================================================

    def test_03_save_initialization(self):
        """save_controlreadings for a watermeter with no non-PR
        readings should create an initialization reading."""
        wm2 = self.env['wua.watermeter'].create({
            'name': 'WM-TESTCR-002',
            'state': 'active',
        })
        self.env['wua.waterconnection'].create({
            'name': 'WC-TESTCR-002',
            'irrigationshed_id': self.irrigationshed.id,
            'position': 2,
            'watermeter_id': wm2.id,
        })

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(50.0, wm2)])

        crs = self.env['wua.controlreading'].search([
            ('watermeter_id', '=', wm2.id)])
        self.assertEqual(len(crs), 1, "Should create one reading")
        self.assertTrue(crs.initialization_reading,
                        "Reading should be initialization")
        self.assertAlmostEqual(crs.volume, 50.0, places=2)

    # ================================================================
    # 4. save_controlreadings — normal (no PR readings)
    # ================================================================

    def test_04_save_normal(self):
        """save_controlreadings with a prior init reading and no PRs
        should create a normal controlreading + controlpresconsumption."""
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])

        crs = self.env['wua.controlreading'].search([
            ('watermeter_id', '=', self.watermeter.id),
            ('initialization_reading', '=', False)])
        self.assertEqual(len(crs), 1, "Should create one non-init reading")
        self.assertAlmostEqual(crs.volume, 200.0, places=2)

        cp = crs.controlpresconsumption_id
        self.assertTrue(cp, "Should have controlpresconsumption")
        # Gross volume = 200 - 100 = 100
        self.assertAlmostEqual(cp.volume, 100.0, places=2,
                               msg="Gross volume = new - previous")

    # ================================================================
    # 5. save_controlreadings — archives prior PR readings
    # ================================================================

    def test_05_save_archives_prior_pr(self):
        """Prior PR readings (reading_time <= now) should be archived
        with adjustement_volume reset to 0."""
        pr = self._create_presresconsumption(self.request_past)
        cr_pr = pr.controlreading_id
        cp_pr = cr_pr.controlpresconsumption_id

        self.assertTrue(cr_pr.active)
        self.assertGreater(cp_pr.adjustement_volume, 0)

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])

        # PR reading should be archived
        cr_refreshed = self.env['wua.controlreading'].with_context(
            active_test=False).browse(cr_pr.id)
        self.assertFalse(cr_refreshed.active,
                         "Prior PR reading should be archived")

    # ================================================================
    # 6. save_controlreadings — deletes/recreates single posterior PR
    # ================================================================

    def test_06_save_recreates_posterior_pr(self):
        """A posterior PR reading (reading_time > now) should be
        deleted and recreated with the new real reading as reference."""
        pr = self._create_presresconsumption(self.request_future)
        old_cr_id = pr.controlreading_id.id

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])

        # Old CR should no longer exist
        old = self.env['wua.controlreading'].with_context(
            active_test=False).search([('id', '=', old_cr_id)])
        self.assertFalse(old.exists(),
                         "Old PR controlreading should be deleted")

        # PR should have a new CR referencing the real reading volume
        pr.invalidate_cache()
        self.assertTrue(pr.controlreading_id,
                        "PR should have a new controlreading")
        self.assertNotEqual(pr.controlreading_id.id, old_cr_id)
        self.assertAlmostEqual(
            pr.controlreading_id.volume, 200.0, places=2,
            msg="Recreated PR should reference real reading volume")

    # ================================================================
    # 7. save_controlreadings — MULTIPLE posterior PRs  (THE BUG CASE)
    # ================================================================

    def test_07_save_multiple_posterior_prs(self):
        """Multiple posterior PR readings should ALL be deleted and
        recreated without is_last_reading / contiguous-range errors
        from the base unlink validation."""
        pr1 = self._create_presresconsumption(
            self.request_future, initial_hour=8.0, watering_duration=2.0)
        pr2 = self._create_presresconsumption(
            self.request_future, initial_hour=12.0, watering_duration=3.0)
        pr3 = self._create_presresconsumption(
            self.request_future, initial_hour=16.0, watering_duration=1.0)

        old_ids = [
            pr1.controlreading_id.id,
            pr2.controlreading_id.id,
            pr3.controlreading_id.id,
        ]

        # This MUST NOT raise an error
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(300.0)])

        # All old CRs should be gone
        for oid in old_ids:
            exists = self.env['wua.controlreading'].with_context(
                active_test=False).search([('id', '=', oid)])
            self.assertFalse(exists.exists(),
                             "Old PR CR %d should be deleted" % oid)

        # All PRs should have new CRs with the real reading volume
        for pr in [pr1, pr2, pr3]:
            pr.invalidate_cache()
            self.assertTrue(pr.controlreading_id,
                            "PR should have a new controlreading")
            self.assertNotIn(pr.controlreading_id.id, old_ids)
            self.assertAlmostEqual(
                pr.controlreading_id.volume, 300.0, places=2,
                msg="Recreated PR should reference real reading volume")

    # ================================================================
    # 8. Different watering durations (crossing reading_times)
    # ================================================================

    def test_08_different_watering_durations(self):
        """PR readings with different durations can have reading_times
        in a different order than creation order. This must work
        without is_last_reading errors.

        PR1: initial_hour=8, duration=8h  → reading_time ≈ 16:00
        PR2: initial_hour=12, duration=1h → reading_time ≈ 13:00

        PR1 reading_time > PR2 reading_time despite PR1 being created
        first. The base unlink would fail because the watermeter's
        last_controlreading_time points to PR1 (the newest by
        reading_time) but iteration might try to delete PR2 first.
        """
        pr1 = self._create_presresconsumption(
            self.request_future, initial_hour=8.0, watering_duration=8.0,
            nominal_flow=5.0)
        pr2 = self._create_presresconsumption(
            self.request_future, initial_hour=12.0, watering_duration=1.0,
            nominal_flow=10.0)

        cr1, cr2 = pr1.controlreading_id, pr2.controlreading_id
        self.assertGreater(
            cr1.reading_time, cr2.reading_time,
            "PR1 should have a later reading_time despite being "
            "created first")

        # Must not raise
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(250.0)])

        for pr in [pr1, pr2]:
            pr.invalidate_cache()
            self.assertTrue(pr.controlreading_id)
            self.assertAlmostEqual(
                pr.controlreading_id.volume, 250.0, places=2)

    # ================================================================
    # 9. Mixed prior and posterior PR readings
    # ================================================================

    def test_09_save_mixed_prior_and_posterior(self):
        """Prior PRs should be archived, posterior should be
        deleted and recreated."""
        pr_past = self._create_presresconsumption(self.request_past)
        cr_past = pr_past.controlreading_id
        pr_future = self._create_presresconsumption(self.request_future)
        old_future_id = pr_future.controlreading_id.id

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])
        # Past → archived
        cr_past_ref = self.env['wua.controlreading'].with_context(
            active_test=False).browse(cr_past.id)
        self.assertFalse(cr_past_ref.active,
                         "Past PR should be archived")
        # Future → deleted and recreated
        pr_future.invalidate_cache()
        self.assertTrue(pr_future.controlreading_id)
        self.assertNotEqual(pr_future.controlreading_id.id, old_future_id)
        self.assertAlmostEqual(
            pr_future.controlreading_id.volume, 200.0, places=2)

    # ================================================================
    # 10. Manual create handles posterior PR readings
    # ================================================================

    def test_10_manual_create_handles_posterior_pr(self):
        """Creating a non-init reading outside save_controlreadings
        (e.g. manual or import) should also delete/recreate posterior
        PR readings."""
        pr = self._create_presresconsumption(self.request_future)
        old_cr_id = pr.controlreading_id.id

        # Manual create (no skip_pr_handling context)
        self.env['wua.controlreading'].create({
            'watermeter_id': self.watermeter.id,
            'reading_time': datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            'volume': 150.0,
            'initialization_reading': False,
            'from_import': True,
        })

        old = self.env['wua.controlreading'].with_context(
            active_test=False).search([('id', '=', old_cr_id)])
        self.assertFalse(old.exists(),
                         "Old PR CR should be deleted")

        pr.invalidate_cache()
        self.assertTrue(pr.controlreading_id)
        self.assertAlmostEqual(
            pr.controlreading_id.volume, 150.0, places=2,
            msg="Recreated PR should reference new reading volume")

    # ================================================================
    # 11. Manual create archives prior PR readings
    # ================================================================

    def test_11_manual_create_archives_prior_pr(self):
        """Creating a non-init reading should archive prior PR
        readings."""
        pr = self._create_presresconsumption(self.request_past)
        cr_pr = pr.controlreading_id
        self.assertTrue(cr_pr.active)

        self.env['wua.controlreading'].create({
            'watermeter_id': self.watermeter.id,
            'reading_time': datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            'volume': 150.0,
            'initialization_reading': False,
            'from_import': True,
        })

        cr_ref = self.env['wua.controlreading'].with_context(
            active_test=False).browse(cr_pr.id)
        self.assertFalse(cr_ref.active,
                         "Prior PR reading should be archived")

    # ================================================================
    # 12. Watermeter last reading tracking after complex operations
    # ================================================================

    def test_12_watermeter_last_reading_correct(self):
        """After save_controlreadings with posterior PRs of different
        durations, watermeter.last_controlreading_time should match
        the actual latest reading_time."""
        # PR1: duration=8h → later reading_time
        self._create_presresconsumption(
            self.request_future, initial_hour=8.0, watering_duration=8.0)
        # PR2: duration=1h → earlier reading_time
        self._create_presresconsumption(
            self.request_future, initial_hour=10.0, watering_duration=1.0)

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(300.0)])

        actual_last = self.env['wua.controlreading'].search([
            ('watermeter_id', '=', self.watermeter.id)],
            order='reading_time desc', limit=1)

        self.watermeter.invalidate_cache()
        self.assertEqual(
            self.watermeter.last_controlreading_time,
            actual_last.reading_time,
            "Watermeter should track the actual latest reading_time")

    # ================================================================
    # 13. Negative reading handling
    # ================================================================

    def test_13_negative_reading(self):
        """A volume lower than the previous reading should create
        a negative.controlreading record instead of a real reading."""
        neg_before = self.env['wua.negative.controlreading'].search_count(
            [('watermeter_id', '=', self.watermeter.id)])

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(50.0)])  # 50 < init 100

        neg_after = self.env['wua.negative.controlreading'].search_count(
            [('watermeter_id', '=', self.watermeter.id)])
        self.assertEqual(neg_after, neg_before + 1,
                         "Should create one negative reading")

        # No non-init reading should have been created
        cr_count = self.env['wua.controlreading'].search_count([
            ('watermeter_id', '=', self.watermeter.id),
            ('initialization_reading', '=', False)])
        self.assertEqual(cr_count, 0,
                         "No normal reading should be created")

    # ================================================================
    # 14. _unlink_presresconsumption_controlreadings helper
    # ================================================================

    def test_14_unlink_helper(self):
        """_unlink_presresconsumption_controlreadings should delete
        controlreadings and their controlpresconsumptions via SQL,
        bypassing base unlink validations."""
        pr1 = self._create_presresconsumption(
            self.request_future, initial_hour=8.0, watering_duration=2.0)
        pr2 = self._create_presresconsumption(
            self.request_future, initial_hour=12.0, watering_duration=3.0)

        cr1, cr2 = pr1.controlreading_id, pr2.controlreading_id
        cp1, cp2 = (cr1.controlpresconsumption_id,
                    cr2.controlpresconsumption_id)

        cr_ids = [cr1.id, cr2.id]
        cp_ids = [cp1.id, cp2.id]

        # Clear FK before deletion (mirrors save_controlreadings flow)
        (pr1 | pr2).write({'controlreading_id': None})

        self.env['wua.controlreading'].\
            _unlink_presresconsumption_controlreadings(cr1 | cr2)

        for cid in cr_ids:
            res = self.env['wua.controlreading'].with_context(
                active_test=False).search([('id', '=', cid)])
            self.assertFalse(res.exists(),
                             "CR %d should be deleted" % cid)

        for cpid in cp_ids:
            res = self.env['wua.controlpresconsumption'].with_context(
                active_test=False).search([('id', '=', cpid)])
            self.assertFalse(res.exists(),
                             "CP %d should be deleted" % cpid)

    # ================================================================
    # 15. _update_watermeter_last_reading helper
    # ================================================================

    def test_15_update_watermeter_helper(self):
        """_update_watermeter_last_reading should correctly refresh
        the watermeter's tracking fields."""
        # Create a second reading
        self.env['wua.controlreading'].with_context(
            skip_pr_handling=True,
        ).create({
            'watermeter_id': self.watermeter.id,
            'reading_time': '2026-02-01 00:00:00',
            'volume': 200.0,
            'initialization_reading': False,
            'from_import': True,
        })

        # Deliberately corrupt watermeter tracking
        self.watermeter.write({
            'last_controlreading_time': '2000-01-01 00:00:00',
            'last_controlreading_value': 0.0,
        })

        self.env['wua.controlreading']._update_watermeter_last_reading(
            self.watermeter)

        self.assertEqual(
            self.watermeter.last_controlreading_time,
            '2026-02-01 00:00:00')
        self.assertAlmostEqual(
            self.watermeter.last_controlreading_value, 200.0, places=2)

    # ================================================================
    # 16. PR auto-creates particularpresconsumptions
    # ================================================================

    def test_16_pr_creates_particularpresconsumptions(self):
        """Creating a presresconsumption should auto-create
        particularpresconsumption records (per parcel, per partner)
        from the controlpresconsumption's volume_real."""
        pr = self._create_presresconsumption(
            self.request_past, initial_hour=8.0,
            watering_duration=2.0, nominal_flow=10.0)

        cp = pr.controlreading_id.controlpresconsumption_id
        ppcs = cp.particularpresconsumption_ids

        self.assertTrue(
            ppcs,
            "Controlpresconsumption should have "
            "particularpresconsumption records")

        # 1 parcel (area=10, 100% of total area),
        # 1 partner (100% water_costs)
        # volume_real = adjustement_volume = 2h * 10 = 20 m³
        expected = 2.0 * 10.0
        total = sum(p.volume_real for p in ppcs)
        self.assertAlmostEqual(
            total, expected, places=2,
            msg="Total ppc volume should equal watering volume")

        for p in ppcs:
            self.assertEqual(p.partner_id, self.partner)
            self.assertEqual(p.parcel_id, self.parcel)

    # ================================================================
    # 17. save_controlreadings: recreated posterior PR has correct ppcs
    # ================================================================

    def test_17_save_recreates_posterior_pr_ppcs(self):
        """After save_controlreadings recreates a posterior PR,
        the new controlpresconsumption should have fresh ppcs
        with the correct watering volume."""
        pr = self._create_presresconsumption(
            self.request_future, initial_hour=8.0,
            watering_duration=2.0, nominal_flow=10.0)
        old_cp = pr.controlreading_id.controlpresconsumption_id
        old_ppc_ids = old_cp.particularpresconsumption_ids.ids

        self.assertTrue(old_ppc_ids,
                        "Before save, ppcs should exist")

        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])

        # Old ppcs should be gone (cascade from SQL delete)
        old_ppcs = self.env['wua.particularpresconsumption'].search(
            [('id', 'in', old_ppc_ids)])
        self.assertFalse(old_ppcs.exists(),
                         "Old ppcs should be deleted")

        # New ppcs should exist with correct volume
        pr.invalidate_cache()
        new_cp = pr.controlreading_id.controlpresconsumption_id
        new_ppcs = new_cp.particularpresconsumption_ids
        self.assertTrue(new_ppcs,
                        "Recreated PR should have new ppcs")

        expected = 2.0 * 10.0
        total = sum(p.volume_real for p in new_ppcs)
        self.assertAlmostEqual(
            total, expected, places=2,
            msg="Recreated ppcs volume should match watering volume")

    # ================================================================
    # 18. Archived prior PR clears ppcs (adjustement_volume=0)
    # ================================================================

    def test_18_archived_prior_pr_clears_ppcs(self):
        """Archiving a prior PR sets adjustement_volume=0, which
        triggers regenerate_particularpresconsumptions. Since
        volume_real becomes 0, no ppcs are created."""
        pr = self._create_presresconsumption(self.request_past)
        cp = pr.controlreading_id.controlpresconsumption_id
        self.assertTrue(cp.particularpresconsumption_ids,
                        "Before archiving, ppcs should exist")
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])
        cp.invalidate_cache()
        self.assertFalse(
            cp.particularpresconsumption_ids,
            "After archiving with adjustement_volume=0, "
            "ppcs should be removed")

    # ================================================================
    # 19. Multiple posterior PRs: all ppcs correct after recreation
    # ================================================================

    def test_19_multiple_posterior_prs_correct_ppcs(self):
        """Multiple posterior PRs with different watering volumes
        should each have correct ppcs after save_controlreadings."""
        pr1 = self._create_presresconsumption(
            self.request_future, initial_hour=8.0,
            watering_duration=2.0, nominal_flow=10.0)   # 20 m³
        pr2 = self._create_presresconsumption(
            self.request_future, initial_hour=12.0,
            watering_duration=3.0, nominal_flow=5.0)    # 15 m³
        pr3 = self._create_presresconsumption(
            self.request_future, initial_hour=16.0,
            watering_duration=1.0, nominal_flow=20.0)   # 20 m³
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(300.0)])
        expected_map = {
            pr1: 20.0,
            pr2: 15.0,
            pr3: 20.0,
        }
        for pr, exp_vol in expected_map.items():
            pr.invalidate_cache()
            cp = pr.controlreading_id.controlpresconsumption_id
            ppcs = cp.particularpresconsumption_ids
            self.assertTrue(
                ppcs,
                "PR should have ppcs after recreation")
            total = sum(p.volume_real for p in ppcs)
            self.assertAlmostEqual(
                total, exp_vol, places=2,
                msg="PR ppcs should have volume %.1f" % exp_vol)

    # ================================================================
    # 20. Quota provisional_extra_consumption reflects all consumption
    # ================================================================

    def test_20_quota_provisional_extra_consumption(self):
        """The quota's provisional_extra_consumption should
        correctly sum all validated ppcs (from both real readings
        and PR readings) within the quota period."""
        self._create_presresconsumption(
            self.request_future, initial_hour=8.0,
            watering_duration=2.0, nominal_flow=10.0)  # 20 m³
        # Before save: only PR ppcs contribute
        self.quota.invalidate_cache()
        self.assertAlmostEqual(
            self.quota.provisional_extra_consumption, 20.0,
            places=2,
            msg="Before save, only PR contributes: 20 m³")
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])
        # After save:
        # - Real reading: 200 - 100 = 100 m³ gross → ppcs 100 m³
        # - Recreated PR: adjustement_volume = 20 → ppcs 20 m³
        # Total: 100 + 20 = 120 m³
        self.quota.invalidate_cache()
        self.assertAlmostEqual(
            self.quota.provisional_extra_consumption, 120.0,
            places=2,
            msg="After save: real (100) + PR (20) = 120 m³")
        # Provisional balance = balance - provisional_extra
        self.assertAlmostEqual(
            self.quota.provisional_balance,
            self.quota.balance - 120.0,
            places=2,
            msg="provisional_balance = balance - 120")

    # ================================================================
    # 21. Mixed prior+posterior: quota reflects correct consumption
    # ================================================================

    def test_21_mixed_quota_correct_consumption(self):
        """After archiving prior PRs and recreating posterior ones,
        the quota should reflect: real reading ppcs + posterior PR
        ppcs (prior archived → adjustement_volume=0 → no ppcs)."""
        pr_past = self._create_presresconsumption(
            self.request_past, initial_hour=8.0,
            watering_duration=2.0, nominal_flow=10.0)  # 20 m³
        pr_future = self._create_presresconsumption(
            self.request_future, initial_hour=10.0,
            watering_duration=3.0, nominal_flow=5.0)   # 15 m³

        # Before save: both PRs contribute
        self.quota.invalidate_cache()
        self.assertAlmostEqual(
            self.quota.provisional_extra_consumption, 35.0,
            places=2,
            msg="Before save: 20 + 15 = 35 m³")
        self.env['wua.controlreading'].save_controlreadings(
            [self._reading_payload(200.0)])
        # After save:
        # - Past PR archived (adj=0) → ppcs deleted → 0 m³
        # - Real reading: 200 - 100 = 100 m³ → ppcs 100 m³
        # - Future PR recreated: 15 m³ → ppcs 15 m³
        # Total: 0 + 100 + 15 = 115 m³
        self.quota.invalidate_cache()
        self.assertAlmostEqual(
            self.quota.provisional_extra_consumption, 115.0,
            places=2,
            msg="After save: real (100) + future PR (15) = 115 m³")
        # Verify the archived PR has no ppcs
        cp_past = pr_past.controlreading_id.controlpresconsumption_id
        cp_past.invalidate_cache()
        self.assertFalse(
            cp_past.particularpresconsumption_ids,
            "Archived PR should have no ppcs")
        # Verify the recreated future PR has correct ppcs
        pr_future.invalidate_cache()
        cp_future = pr_future.controlreading_id.controlpresconsumption_id
        ppcs_future = cp_future.particularpresconsumption_ids
        self.assertAlmostEqual(
            sum(p.volume_real for p in ppcs_future), 15.0,
            places=2,
            msg="Future PR ppcs should be 15 m³")
