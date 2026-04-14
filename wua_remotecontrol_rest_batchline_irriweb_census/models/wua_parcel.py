# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re
import requests
import json
import psycopg2
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

_ENDPOINT_PARCELS = '/api/gestion/parcelas'
_BATCH_SIZE = 500

_RE_NOMBRE_LEADING_NUMBER = re.compile(r'^(\d+)(?=\s|$)')


def _safe_str(e):
    """Python 2 safe conversion of exception to unicode string."""
    try:
        return unicode(e)
    except (UnicodeDecodeError, UnicodeEncodeError):
        return repr(e)


def _clean(value):
    if isinstance(value, basestring):
        return value.strip()
    return value or ''


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    from_irriweb_census = fields.Boolean(
        string='From IrriWEB Census',
        default=False,
        index=True,
        help='Set to True when this parcel was created or imported '
             'by the IrriWEB census synchronisation.')

    id_irriweb = fields.Integer(
        string='IrriWEB ID',
        default=0,
        index=True,
        help='Numeric identifier from the IrriWEB census API '
             '(the ``identificador`` field). '
             'Hidden field used for traceability and deduplication.')

    # ------------------------------------------------------------------
    # Fetch from IrriWEB
    # ------------------------------------------------------------------

    @api.model
    def fetch_all_parcels_from_batchline(self, url, token):
        """GET /api/gestion/parcelas — returns (list, error_message).

        *token* is ignored; authentication is via API key header
        (read from configuration by _get_census_request_headers).
        """
        records = []
        error_message = ''
        headers, err = self.env['res.partner']._get_census_request_headers()
        if not headers:
            return records, err
        try:
            resp = requests.get(url + _ENDPOINT_PARCELS, headers=headers)
            if resp.status_code == 200:
                records = json.loads(resp.text)
            else:
                error_message = resp.text
        except Exception as e:
            error_message = _('Telecontrol Error: could not fetch parcels. '
                              '%s') % _safe_str(e)
        return records, error_message

    @api.model
    def fetch_single_parcel_from_batchline(self, url, token, parcel_id):
        """GET /api/gestion/parcelas/{id} — returns (dict|None, error_message).

        *token* is ignored; authentication is via API key header.
        """
        record = None
        error_message = ''
        headers, err = self.env['res.partner']._get_census_request_headers()
        if not headers:
            return record, err
        try:
            resp = requests.get(
                '%s%s/%s' % (url, _ENDPOINT_PARCELS, parcel_id),
                headers=headers)
            if resp.status_code == 200:
                record = json.loads(resp.text)
            else:
                error_message = resp.text
        except Exception as e:
            error_message = _('Telecontrol Error: could not fetch parcel %s. '
                              '%s') % (parcel_id, _safe_str(e))
        return record, error_message

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    @api.model
    def _map_batchline_census_parcel_vals(self, remote):
        """Convert a remote IrriWEB *parcel* dict to Odoo field values.

        Confirmed IrriWEB JSON field mapping:
            identificador   -> id_irriweb  (stored for traceability, NOT used
                                            as the match/lookup key)
            nombre          -> extra_code  (PIVOT KEY — used to find existing
                                            parcels in Odoo; also written to
                                            name when creating new parcels;
                                            normalised: leading integer is
                                            extracted when nombre starts with
                                            digits, e.g. "4045 (Finca X)"→"4045")
            refCatastral    -> cadastral_reference  (may be null)
            superficie      -> area_official  (area in ha)
            paraje          -> rurallocation name (Many2one, resolved separately)
            tipo            -> parcel_type  (0 = 'R' rustic, 1 = 'U' urban)

        Returns a dict of Odoo field values.  Resolution of Many2one fields
        (county, rurallocation) and linked records (partnerlinks,
        irrigationpointwc) is handled by the upsert method.
        """
        irriweb_id = remote.get('identificador')
        parcel_name = _clean(
            remote.get('nombre') or (str(irriweb_id) if irriweb_id else ''))
        # Normalise: "4045 (Finca La Jarilla)" → "4045".
        # Names that don't start with a bare integer are left unchanged.
        _m = _RE_NOMBRE_LEADING_NUMBER.match(parcel_name)
        if _m:
            parcel_name = _m.group(1)
        cadastral_ref = _clean(remote.get('refCatastral') or '')
        area = remote.get('superficie') or 0.0

        # parcel_type: IrriWEB sends an integer (0 = rustic, 1 = urban)
        parcel_type_raw = remote.get('tipo')
        if parcel_type_raw == 1:
            type_code = 'U'
        else:
            type_code = 'R'

        vals = {
            'extra_code': parcel_name[:40],  # SIZE = 40 — same value as name
            'id_irriweb': int(irriweb_id) if irriweb_id else 0,
            'name': parcel_name[:20],      # SIZE_NAME = 20
            'area_official': float(area),
            'parcel_type': type_code,
        }
        # Only set cadastral_reference when IrriWEB sends exactly 14 chars
        # (base_wua SIZE_CADASTRAL_REFERENCE constraint).
        if len(cadastral_ref) == 14:
            vals['cadastral_reference'] = cadastral_ref
        return vals, remote

    # ------------------------------------------------------------------
    # Resolve helpers  (Many2one lookups)
    # ------------------------------------------------------------------

    @api.model
    def _get_or_create_rurallocation(self, name):
        """Return a wua.rurallocation id matching *name*, creating if needed."""
        if not name:
            return False
        existing = self.env['wua.rurallocation'].search(
            [('name', '=', name)], limit=1)
        if existing:
            return existing.id
        new = self.env['wua.rurallocation'].create({
            'name': name,
            'description': False,
        })
        return new.id

    @api.model
    def _get_default_county_id(self):
        """Return the first available county id as fallback."""
        county = self.env['wua.region.state.county'].search([], limit=1)
        return county.id if county else False

    @api.model
    def _create_parcel_with_name_fallback(self, vals, warn_sink=None):
        """Create a ``wua.parcel``, retrying with ``extra_code`` as name on
        duplicate-name constraint violation (``wua_parcel_unique_name``).
        """
        ctx = {'no_update_partners': True, 'no_test': True}
        try:
            with self.env.cr.savepoint():
                return self.with_context(**ctx).create(
                    dict(vals, from_irriweb_census=True))
        except (ValidationError, psycopg2.IntegrityError):
            original_name = vals.get('name', '')
            extra_code = vals.get('extra_code', '')
            fallback_name = extra_code[:20]
            msg = _(
                'Duplicate parcel name "%s" (extra_code=%s) '
                '\u2014 created with name "%s".') % (
                    original_name, extra_code, fallback_name)
            _logger.warning(u'Batchline census sync: %s', msg)
            if warn_sink is not None:
                warn_sink.append(('warning_parcel', msg))
            vals_alt = dict(vals, name=fallback_name, from_irriweb_census=True)
            return self.with_context(**ctx).create(vals_alt)

    # ------------------------------------------------------------------
    # Upsert parcel
    # ------------------------------------------------------------------

    @api.model
    def _upsert_batchline_census_parcel(self, vals, remote,
                                        existing_parcel_by_extra_code=None,
                                        warn_sink=None,
                                        toma_sink=None,
                                        wc_cache=None):
        """Create or enrich a ``wua.parcel`` from IrriWEB census values.

        Match logic (pivot key: ``extra_code`` = IrriWEB ``nombre``):
          1. Parcel whose ``extra_code`` matches the IrriWEB ``nombre``
             already exists in Odoo (manually created before the census sync).
             Leave ``from_irriweb_census`` unchanged and sync partner/water links.
          2. No match → create a new parcel with ``name`` = ``extra_code``
             = IrriWEB ``nombre`` and ``from_irriweb_census=True``.

        ``id_irriweb`` (the IrriWEB ``identificador``) is always stored for
        traceability but is NOT used as the lookup key.

        Returns ``True`` if a new record was created, ``False`` otherwise.
        """
        extra_code = vals.get('extra_code') or ''
        if not extra_code:
            msg = _(
                'IrriWEB record identificador=%s has empty nombre '
                '\u2014 parcel skipped.') % (vals.get('id_irriweb') or '?')
            _logger.warning(u'Batchline census: %s', msg)
            if warn_sink is not None:
                warn_sink.append(('warning_parcel', msg))
            return False

        # --- Look up existing parcel by extra_code ---
        if existing_parcel_by_extra_code is not None:
            existing_parcel = existing_parcel_by_extra_code.get(extra_code)
        else:
            existing_parcel = self.with_context(active_test=False).search(
                [('extra_code', '=', extra_code)], limit=1) or False

        if existing_parcel:
            # Case 1: parcel already exists (may be manual or from a
            # previous sync run).  Do NOT touch from_irriweb_census — it
            # already holds the correct value set at creation time.
            ctx = {'no_update_partners': True, 'no_test': True}
            update_vals = {}
            # Fill rurallocation_id from IrriWEB 'paraje' only when the parcel
            # does not have one yet.
            if not existing_parcel.rurallocation_id:
                farm_location = _clean(remote.get('paraje') or '')
                if farm_location:
                    rl_id = self._get_or_create_rurallocation(farm_location)
                    if rl_id:
                        update_vals['rurallocation_id'] = rl_id
            # Only call write() when there is actually something to update.
            # write({}) still fires base_wua's subparcel-area constraint, which
            # can fail on parcels whose existing data is already inconsistent.
            if update_vals:
                try:
                    with self.env.cr.savepoint():
                        existing_parcel.with_context(**ctx).write(update_vals)
                except UserError as e:
                    msg = _('Parcel "%s": could not update fields %s — '
                            'pre-existing data inconsistency: %s') % (
                                existing_parcel.name,
                                list(update_vals.keys()),
                                e.name)
                    _logger.warning(u'Batchline census sync: %s', msg)
                    if warn_sink is not None:
                        warn_sink.append(('warning_parcel', msg))
            self._sync_batchline_parcel_partnerlinks(
                existing_parcel, remote, warn_sink=warn_sink)
            self._sync_batchline_parcel_waterconnections(
                existing_parcel, remote, toma_sink=toma_sink,
                wc_cache=wc_cache)
            return False

        # Case 2: not found → create a new parcel from IrriWEB.
        # Resolve rurallocation from 'paraje' (rural location name).
        farm_location = _clean(remote.get('paraje') or '')
        if farm_location:
            vals['rurallocation_id'] = self._get_or_create_rurallocation(
                farm_location)

        # county_id is required — use default if not mappable.
        if 'county_id' not in vals:
            vals['county_id'] = self._get_default_county_id()

        # base_wua create() accesses these keys directly (no .get()), set defaults.
        vals.setdefault('cadastral_sector', 'A')
        vals.setdefault('cadastral_polygon', False)
        vals.setdefault('cadastral_parcel', False)
        vals.setdefault('cadastral_reference', False)

        parcel = self._create_parcel_with_name_fallback(vals, warn_sink)

        # Add to cache so subsequent records in the same run find it via Case 1.
        if existing_parcel_by_extra_code is not None:
            existing_parcel_by_extra_code[parcel.extra_code] = parcel

        self._sync_batchline_parcel_partnerlinks(
            parcel, remote, warn_sink=warn_sink)
        self._sync_batchline_parcel_waterconnections(
            parcel, remote, toma_sink=toma_sink, wc_cache=wc_cache)

        return True

    # ------------------------------------------------------------------
    # Partner links  (owner / irrigator / percentage)
    # ------------------------------------------------------------------

    @api.model
    def _sync_batchline_parcel_partnerlinks(self, parcel, remote,
                                            warn_sink=None):
        """Sync ``wua.parcel.partnerlink`` records for *parcel*.

        IrriWEB JSON: ``propietarios`` → profile='O',
                      ``explotadores`` → profile='L'.
        Note: IrriWEB uses "portentaje" (typo for "percentage") — ignored;
        percentages are derived from the business rules below.

        Two casuistics:

        **Case A — same identificador in propietarios AND explotadores:**
          → ONE record, profile='O', irrigation_partner=True,
            ownership/water/other = 100 / 100 / 100.

        **Case B — different identificadores:**
          → Owner record:  profile='O', irrigation_partner=False,
                           ownership/water/other = 100 / 0 / 0.
          → Lessee record: profile='L', irrigation_partner=True,
                           ownership/water/other = 0 / 100 / 100.

        Full reconciliation:
        - Active links absent from IrriWEB are archived (``active=False``).
        - Archived links that reappear in IrriWEB are reactivated.
        - ``partnerlink_code`` (``<parcel.name>-<pos:02d>``) and
          ``area_official`` are set on new links and backfilled on existing
          ones that are missing them.

        If IrriWEB sends neither ``propietarios`` nor ``explotadores`` the
        method returns immediately without touching existing links (a warning
        is appended to *warn_sink* so the operator is informed).
        """
        # Early exit: no partner data from IrriWEB — leave parcel untouched.
        if not (remote.get('propietarios') or []) \
                and not (remote.get('explotadores') or []):
            msg = _(
                'Parcel "%s" has no propietarios or explotadores in '
                'IrriWEB \u2014 no partnerlinks created/updated.') % (
                    parcel.extra_code)
            _logger.warning(u'Batchline census: %s', msg)
            if warn_sink is not None:
                warn_sink.append(('warning_parcel', msg))
            return

        Partner = self.env['res.partner']
        Partnerlink = self.env['wua.parcel.partnerlink']

        # ----------------------------------------------------------
        # Step 1 — classify IrriWEB entries as dual-role / pure owner
        #          / pure lessee, preserving the original API order.
        # ----------------------------------------------------------
        owner_codes = []     # ordered; deduped
        lessee_codes = []    # ordered; deduped
        _seen_o = set()
        _seen_l = set()

        for d in (remote.get('propietarios') or []):
            pc = d.get('identificador')
            if not pc:
                msg = _(
                    'Parcel "%s": propietarios entry has no identificador '
                    '\u2014 skipped.') % parcel.extra_code
                _logger.warning(u'Batchline census: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(('warning_partnerlink', msg))
                continue
            if pc not in _seen_o:
                _seen_o.add(pc)
                owner_codes.append(pc)

        for d in (remote.get('explotadores') or []):
            pc = d.get('identificador')
            if not pc:
                msg = _(
                    'Parcel "%s": explotadores entry has no identificador '
                    '\u2014 skipped.') % parcel.extra_code
                _logger.warning(u'Batchline census: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(('warning_partnerlink', msg))
                continue
            if pc not in _seen_l:
                _seen_l.add(pc)
                lessee_codes.append(pc)

        dual_codes = _seen_o & _seen_l         # same person in both lists
        pure_owner_codes = _seen_o - dual_codes
        pure_lessee_codes = _seen_l - dual_codes

        # Build the canonical list of links to upsert, in a deterministic
        # order: dual-role owners first (from propietarios order), then
        # pure owners, then pure lessees (from explotadores order).
        links_to_process = []

        for pc in owner_codes:
            if pc in dual_codes:
                # Case A: same person is both owner and irrigator.
                links_to_process.append({
                    'partner_code': pc,
                    'profile': 'O',
                    'ownership_percentage': 100.0,
                    'water_costs_percentage': 100.0,
                    'other_costs_percentage': 100.0,
                    '_is_dual': True,
                })
            else:
                # Case B — pure owner: owns the land, does not irrigate.
                links_to_process.append({
                    'partner_code': pc,
                    'profile': 'O',
                    'ownership_percentage': 100.0,
                    'water_costs_percentage': 0.0,
                    'other_costs_percentage': 0.0,
                    '_is_dual': False,
                })

        for pc in lessee_codes:
            if pc in pure_lessee_codes:
                # Case B — pure lessee: irrigates but does not own.
                links_to_process.append({
                    'partner_code': pc,
                    'profile': 'L',
                    'ownership_percentage': 0.0,
                    'water_costs_percentage': 100.0,
                    'other_costs_percentage': 100.0,
                    '_is_dual': False,
                })
            # dual-role codes are already in the owner loop above — skip.

        # ----------------------------------------------------------
        # Step 2 — resolve partner records; warn and skip unknowns
        # ----------------------------------------------------------
        resolved_links = []  # [(partner_record, link_data_dict), ...]
        missing_partner_codes = []
        for link_data in links_to_process:
            partner_code = link_data['partner_code']
            partner = Partner.with_context(active_test=False).search(
                [('partner_code', '=', partner_code)], limit=1)
            if not partner:
                missing_partner_codes.append(partner_code)
                msg = _(
                    'Partner %s not found for parcel %s '
                    '\u2014 partnerlink skipped.') % (
                        partner_code, parcel.extra_code)
                _logger.warning(u'Batchline census: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(('warning_partnerlink', msg))
                continue
            resolved_links.append((partner, link_data))

        # If IrriWEB provided partner codes but none were found in Odoo,
        # add an explicit summary warning so it is visible in the log
        # independently of the per-code warnings emitted above.
        if links_to_process and not resolved_links:
            missing_codes_txt = u', '.join(
                unicode(c) for c in missing_partner_codes)
            msg = _(
                'Parcel "%s": all %d partner code(s) from IrriWEB not '
                'found in Odoo (%s) \u2014 no partnerlinks '
                'created/updated.') % (
                    parcel.extra_code, len(links_to_process),
                    missing_codes_txt)
            _logger.warning(u'Batchline census: %s', msg)
            if warn_sink is not None:
                warn_sink.append(('warning_partnerlink', msg))

        # ----------------------------------------------------------
        # Step 3 — assign irrigation_partner (exactly one per parcel)
        #
        # Priority: first pure lessee → first dual-role owner →
        #           first pure owner (fallback when no lessees exist).
        # ----------------------------------------------------------
        irrigation_partner_id = False
        # Priority 1: first pure lessee
        for partner, link_data in resolved_links:
            if link_data['profile'] == 'L':
                irrigation_partner_id = partner.id
                break
        # Priority 2: first dual-role owner (Case A, no separate lessee)
        if not irrigation_partner_id:
            for partner, link_data in resolved_links:
                if link_data['_is_dual']:
                    irrigation_partner_id = partner.id
                    break
        # Priority 3: first pure owner (only owners, no lessees at all)
        if not irrigation_partner_id:
            for partner, link_data in resolved_links:
                if link_data['profile'] == 'O':
                    irrigation_partner_id = partner.id
                    break

        # IrriWEB keys present in this run — used for stale detection.
        irriweb_keys = frozenset(
            (partner.id, link_data['profile'])
            for partner, link_data in resolved_links
        )

        # ----------------------------------------------------------
        # Step 4 — load ALL existing links (active + archived) once
        # ----------------------------------------------------------
        all_existing = Partnerlink.with_context(active_test=False).search(
            [('parcel_id', '=', parcel.id)])

        # pos counter must account for archived links to avoid reuse.
        existing_pos = [pl.pos for pl in all_existing if pl.pos]
        pos_counter = max(existing_pos) if existing_pos else 0

        # Lookup dict: (partner_id, profile) → partnerlink record
        existing_by_key = {
            (pl.partner_id.id, pl.profile): pl
            for pl in all_existing
        }

        # ----------------------------------------------------------
        # Step 5 — upsert resolved links
        # ----------------------------------------------------------
        for partner, link_data in resolved_links:
            is_manager = (partner.id == irrigation_partner_id)
            link_vals = {
                'ownership_percentage': link_data['ownership_percentage'],
                'water_costs_percentage': link_data['water_costs_percentage'],
                'other_costs_percentage': link_data['other_costs_percentage'],
                'irrigation_partner': is_manager,
                'area_official': parcel.area_official,
            }

            key = (partner.id, link_data['profile'])
            existing_link = existing_by_key.get(key)

            if existing_link:
                # Reactivate if previously archived.
                if not existing_link.active:
                    link_vals['active'] = True
                # Backfill partnerlink_code if it was never set.
                if not existing_link.partnerlink_code:
                    link_vals['partnerlink_code'] = (
                        parcel.name + '-' +
                        str(existing_link.pos).zfill(2))
                existing_link.write(link_vals)
            else:
                pos_counter += 1
                link_vals.update({
                    'parcel_id': parcel.id,
                    'partner_id': partner.id,
                    'profile': link_data['profile'],
                    'pos': pos_counter,
                    'partnerlink_code': (
                        parcel.name + '-' +
                        str(pos_counter).zfill(2)),
                })
                new_link = Partnerlink.create(link_vals)
                # Keep cache current so the archive step sees the new link.
                existing_by_key[key] = new_link

        # ----------------------------------------------------------
        # Step 6 — archive stale links (active but absent from IrriWEB)
        # ----------------------------------------------------------
        for key, existing_link in existing_by_key.items():
            if key not in irriweb_keys and existing_link.active:
                existing_link.write({'active': False})
                msg = _(
                    'Partnerlink (partner_id=%d, profile=%s) archived for '
                    'parcel %s \u2014 no longer present in IrriWEB.') % (
                        key[0], key[1], parcel.extra_code)
                _logger.warning(u'Batchline census: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(('warning_partnerlink', msg))

    # ------------------------------------------------------------------
    # Water connection links
    # ------------------------------------------------------------------

    @api.model
    def _build_waterconnection_name(self, hidrante, toma_int):
        """Build the Odoo waterconnection name from IrriWEB hidrante + toma.

        Valle Inferior naming convention (hardcoded — this module is only
        installed on Valle Inferior):

        * If ``hidrante`` already starts with ``"ARQ-"`` (the hydrant number
          is already qualified), append the toma zero-padded to 2 digits::

              "ARQ-3409" + 1  →  "ARQ-3409-01"
              "ARQ-0459" + 1  →  "ARQ-0459-01"

        * If ``hidrante`` is a bare number (no prefix), prepend ``"ARQ-"``
          and zero-pad the number to 4 digits::

              "794" + 1  →  "ARQ-0794-01"
              "601" + 1  →  "ARQ-0601-01"
        """
        if hidrante.upper().startswith(u'ARQ-'):
            return u'%s-%02d' % (hidrante, toma_int)
        # Bare number — zero-pad to 4 digits and add the ARQ prefix.
        try:
            num = int(hidrante)
            return u'ARQ-%04d-%02d' % (num, toma_int)
        except ValueError:
            # Not a plain integer either — fall back to simple concatenation
            # and let the lookup fail gracefully with a toma warning.
            return u'ARQ-%s-%02d' % (hidrante, toma_int)

    @api.model
    def _sync_batchline_parcel_waterconnections(self, parcel, remote,
                                                toma_sink=None,
                                                wc_cache=None):
        """Sync ``wua.parcel.irrigationpointwc`` records for *parcel*.

        IrriWEB JSON: ``hidrantes`` list of ``{hidrante, toma}`` where
        ``hidrante`` is the hydrant identifier and ``toma`` is the outlet
        number.  The Odoo waterconnection name is built by
        :meth:`_build_waterconnection_name`.

        **No records are created by this method** — only lookups against
        existing ``wua.waterconnection`` records are performed.  If a
        matching waterconnection is found it is linked to the parcel; if
        it is not found a warning is appended to *toma_sink* (displayed
        on the dedicated "Tomas" page of the sync log, separate from
        regular errors/warnings).

        Idempotency: if the parcel is already linked to the
        waterconnection the entry is silently skipped on subsequent sync
        runs.
        """
        shed_entries = remote.get('hidrantes') or []
        if not shed_entries:
            return

        WC = self.env['wua.waterconnection']
        Ipwc = self.env['wua.parcel.irrigationpointwc']
        IrrPt = self.env['wua.parcel.irrigationpoint']

        pos_counter = max(
            [ip.pos for ip in parcel.irrigationpointwc_ids] or [0])

        for item in shed_entries:
            hidrante = _clean(item.get('hidrante') or '')
            toma = item.get('toma')
            if not hidrante:
                msg = _(
                    'Parcel "%s": hidrantes entry has no hidrante value '
                    '\u2014 toma skipped.') % parcel.extra_code
                _logger.warning(u'Batchline census: %s', msg)
                if toma_sink is not None:
                    toma_sink.append(msg)
                continue

            try:
                toma_int = int(toma)
            except (TypeError, ValueError):
                toma_int = 0

            if toma_int <= 0:
                msg = _(
                    'Toma value "%s" for hidrante "%s" (parcel %s) is '
                    'not a positive integer \u2014 skipped.') % (
                        toma, hidrante, parcel.extra_code)
                _logger.warning(u'Batchline census: %s', msg)
                if toma_sink is not None:
                    toma_sink.append(msg)
                continue

            wc_name = self._build_waterconnection_name(hidrante, toma_int)

            # 1. Lookup waterconnection — no creation.
            if wc_cache is not None:
                wc = wc_cache.get(wc_name) or False
            else:
                wc = WC.search([('name', '=', wc_name)], limit=1) or False

            if not wc:
                msg = _(
                    'Waterconnection "%s" not found in Odoo '
                    '(parcel %s) \u2014 no link created.') % (
                        wc_name, parcel.extra_code)
                _logger.warning(u'Batchline census: %s', msg)
                if toma_sink is not None:
                    toma_sink.append(msg)
                continue

            # 2. Idempotency: skip silently if already linked.
            existing_ip = Ipwc.search([
                ('parcel_id', '=', parcel.id),
                ('waterconnection_id', '=', wc.id),
            ], limit=1)
            if existing_ip:
                continue

            # 3. Create the link records.
            pos_counter += 1
            Ipwc.create({
                'parcel_id': parcel.id,
                'waterconnection_id': wc.id,
                'pos': pos_counter,
            })
            # Also create the mirrored irrigationpoint record (normally
            # done by wua.parcel.write() ORM hook, bypassed here).
            existing_irr_pt = IrrPt.search([
                ('parcel_id', '=', parcel.id),
                ('waterconnection_id', '=', wc.id),
            ], limit=1)
            if not existing_irr_pt:
                IrrPt.create({
                    'parcel_id': parcel.id,
                    'type': 'WC',
                    'waterconnection_id': wc.id,
                })

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    @api.model
    def action_census_sync_parcels_batchline(self, log=None):
        """Fetch all parcels from IrriWEB and upsert them into Odoo.

        Can be called standalone or from inside
        ``_run_census_sync_batchline`` (in which case *log* is provided).

        Returns a dict with counts: ``{'created': int, 'skipped': int,
        'warnings': int, 'errors': int}``.
        """
        Partner = self.env['res.partner']

        url, _header, _value = Partner._get_census_connection_params()
        if not url:
            msg = _('Census API URL not configured '
                    '(url_census_rest_batchline).')
            if log:
                Partner._census_sync_log_line(
                    log, _ENDPOINT_PARCELS, '', msg, level='error')
                self.env.cr.commit()
            return {'created': 0, 'skipped': 0, 'warnings': 0,
                    'tomas': 0, 'errors': 1}

        records, err = self.fetch_all_parcels_from_batchline(url, None)
        if err:
            if log:
                Partner._census_sync_log_line(
                    log, _ENDPOINT_PARCELS, '', err, level='error')
                self.env.cr.commit()
            return {'created': 0, 'skipped': 0, 'warnings': 0,
                    'tomas': 0, 'errors': 1}

        total = len(records)
        created = 0
        skipped = 0
        warnings = 0
        warning_parcel = 0
        warning_partnerlink = 0
        tomas = 0
        errors = 0

        _logger.info(
            'Batchline census sync: %d parcels to process', total)

        # Pre-load existing parcels by extra_code for O(1) lookup.
        # extra_code = IrriWEB nombre — this is the pivot/link key.
        all_existing_parcels = self.with_context(active_test=False).search([])
        existing_parcel_by_extra_code = {
            p.extra_code: p for p in all_existing_parcels if p.extra_code
        }
        # Snapshot of pre-existing Odoo extra_codes used after the loop to
        # detect parcels that exist in Odoo but are absent from IrriWEB.
        odoo_extra_codes_before = set(existing_parcel_by_extra_code.keys())
        _logger.info(
            'Batchline census sync (parcels): %d existing parcels pre-loaded '
            'by extra_code', len(existing_parcel_by_extra_code))

        # Build the set of extra_codes present in IrriWEB so we can warn
        # about Odoo parcels that have no counterpart in IrriWEB.
        # Apply the same nombre normalisation used in _map_batchline_census_parcel_vals
        # so that "4045 (Finca La Jarilla)" and stored extra_code "4045" match.
        irriweb_extra_codes = set()
        for _r in records:
            _irriweb_id = _r.get('identificador')
            _nombre = _clean(
                _r.get('nombre') or (str(_irriweb_id) if _irriweb_id else ''))
            _m = _RE_NOMBRE_LEADING_NUMBER.match(_nombre)
            if _m:
                _nombre = _m.group(1)
            if _nombre:
                irriweb_extra_codes.add(_nombre[:40])

        # Pre-load waterconnection cache for O(1) lookups.
        wc_cache = {
            w.name: w
            for w in self.env['wua.waterconnection'].with_context(
                active_test=False).search([])
        }
        _logger.info(
            'Batchline census sync: %d waterconnections pre-loaded',
            len(wc_cache))

        _LOG_INTERVAL = 100  # log progress every N parcels within a batch

        for batch_start in range(0, total, _BATCH_SIZE):
            batch = records[batch_start:batch_start + _BATCH_SIZE]
            for idx, remote in enumerate(batch):
                remote_id = remote.get('identificador', '')
                # Log progress every _LOG_INTERVAL records within the batch
                # so the operator can see the process is still running.
                if idx > 0 and idx % _LOG_INTERVAL == 0:
                    _logger.info(
                        'Batchline census sync (parcels): processing '
                        '%d / %d (batch offset %d)',
                        batch_start + idx, total, idx)
                try:
                    vals, _remote = self._map_batchline_census_parcel_vals(remote)
                    # Defensive: ensure we don't pass unknown fields like
                    # 'description' to wua.parcel.create()/write() which
                    # triggers Odoo warnings if the field isn't in the model.
                    vals.pop('description', None)
                    warn_sink = []
                    toma_sink = []
                    with self.env.cr.savepoint():
                        is_new = self._upsert_batchline_census_parcel(
                            vals, remote,
                            existing_parcel_by_extra_code=existing_parcel_by_extra_code,
                            warn_sink=warn_sink,
                            toma_sink=toma_sink,
                            wc_cache=wc_cache)
                    # Record-level warnings
                    for w_level, w_msg in warn_sink:
                        warnings += 1
                        if w_level == 'warning_parcel':
                            warning_parcel += 1
                        elif w_level == 'warning_partnerlink':
                            warning_partnerlink += 1
                        if log:
                            Partner._census_sync_log_line(
                                log, _ENDPOINT_PARCELS, remote_id, w_msg,
                                level=w_level)
                    # Toma (waterconnection not found) notices
                    for t in toma_sink:
                        tomas += 1
                        if log:
                            Partner._census_sync_log_line(
                                log, _ENDPOINT_PARCELS, remote_id, t,
                                level='toma')
                    if is_new:
                        created += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    msg = _safe_str(e)
                    _logger.error(
                        'Batchline census sync: error on parcel %s. %s',
                        remote_id, msg)
                    if log:
                        Partner._census_sync_log_line(
                            log, _ENDPOINT_PARCELS, remote_id, msg,
                            level='error')
                    wc_cache.clear()
                    wc_cache.update({
                        w.name: w
                        for w in self.env['wua.waterconnection'].with_context(
                            active_test=False).search([])
                    })
                    _logger.info(
                        'Batchline census sync: wc_cache rebuilt after error '
                        'on parcel %s (%d waterconnections)',
                        remote_id, len(wc_cache))

            self.env.cr.commit()
            self.invalidate_cache()

            batch_end = batch_start + len(batch)
            _logger.info(
                'Batchline census sync (parcels): %d / %d processed '
                '(created=%d, skipped=%d, warnings=%d, tomas=%d, '
                'errors=%d)',
                batch_end, total, created, skipped, warnings, tomas, errors)
            if log:
                Partner._update_census_sync_log_safe(log.id, {
                    'summary': _('Processing parcels: %d / %d') % (
                        batch_end, total),
                })

        # Warn about Odoo parcels that have no counterpart in IrriWEB.
        # These parcels are left untouched; the warning is for traceability.
        for ec in sorted(odoo_extra_codes_before):
            if ec not in irriweb_extra_codes:
                orphan = existing_parcel_by_extra_code.get(ec)
                msg = _(
                    'Parcel extra_code="%s" (id=%d) exists in Odoo but '
                    'has no matching record in IrriWEB \u2014 no action '
                    'taken.') % (ec, orphan.id if orphan else 0)
                warnings += 1
                warning_parcel += 1
                _logger.warning(u'Batchline census: %s', msg)
                if log:
                    Partner._census_sync_log_line(
                        log, _ENDPOINT_PARCELS, ec, msg,
                        level='warning_parcel')

        _logger.info(
            'Batchline census sync (parcels) finished: created=%d, '
            'skipped=%d, warnings=%d (parcel=%d, partnerlink=%d), '
            'tomas=%d, errors=%d',
            created, skipped, warnings, warning_parcel,
            warning_partnerlink, tomas, errors)
        return {
            'created': created,
            'skipped': skipped,
            'warnings': warnings,
            'warning_parcel': warning_parcel,
            'warning_partnerlink': warning_partnerlink,
            'tomas': tomas,
            'errors': errors,
        }
