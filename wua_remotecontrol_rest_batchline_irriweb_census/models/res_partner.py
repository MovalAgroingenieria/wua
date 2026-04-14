# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

_BATCH_SIZE = 500
_ENDPOINT_PARTNERS = '/api/gestion/regantes'


def _safe_str(e):
    """Python 2 safe conversion of exception to unicode string."""
    try:
        return unicode(e)
    except (UnicodeDecodeError, UnicodeEncodeError):
        return repr(e)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    from_irriweb_census = fields.Boolean(
        string='From IrriWEB Census',
        default=False,
        index=True,
        help='Set to True when this partner was created or imported '
             'by the IrriWEB census synchronisation.')

    id_irriweb = fields.Integer(
        string='IrriWEB ID',
        default=0,
        index=True,
        help='Numeric identifier from the IrriWEB census API. '
             'Hidden field used for traceability and deduplication.')

    # ------------------------------------------------------------------
    # Connection helpers  (Census API — API key, not user/password token)
    # ------------------------------------------------------------------

    @api.model
    def _get_census_connection_params(self):
        """Return (url, apikey_header, apikey_value) from configuration.

        These are the Census-specific parameters defined by THIS module,
        separate from the parent module's token-based connection.
        Returns (None, None, None) if the URL is not configured.
        """
        get = self.env['ir.values'].get_default
        url = get('wua.irrigation.configuration',
                  'url_census_rest_batchline')
        header = get('wua.irrigation.configuration',
                     'census_apikey_header_batchline') or 'X-Api-Key'
        value = get('wua.irrigation.configuration',
                    'census_apikey_value_batchline')
        if url:
            return url.rstrip('/'), header, value
        return None, None, None

    @api.model
    def _get_census_request_headers(self):
        """Build the HTTP headers dict for Census API requests.

        Returns (headers_dict, error_message).
        """
        url, header, value = self._get_census_connection_params()
        if not url:
            return None, _('Census API URL not configured '
                           '(url_census_rest_batchline).')
        headers = {'content-type': 'application/json'}
        if header and value:
            headers[header] = value
        return headers, ''

    # ------------------------------------------------------------------
    # Fetch from IrriWEB
    # ------------------------------------------------------------------

    @api.model
    def fetch_all_partners_from_batchline(self, url, token):
        """GET /api/gestion/regantes (IrriWEB irrigators endpoint) — returns (list, error_message).

        *token* is ignored; authentication is via API key header.
        Kept for backward-compatible signature.
        """
        records = []
        error_message = ''
        headers, err = self._get_census_request_headers()
        if not headers:
            return records, err
        try:
            resp = requests.get(url + _ENDPOINT_PARTNERS, headers=headers)
            if resp.status_code == 200:
                records = json.loads(resp.text)
            else:
                error_message = resp.text
        except Exception as e:
            error_message = _('Telecontrol Error: could not fetch partners. '
                              '%s') % _safe_str(e)
        return records, error_message

    @api.model
    def fetch_single_partner_from_batchline(self, url, token, remote_id):
        """GET /api/gestion/regantes/{id} (IrriWEB irrigator by ID) — returns (dict|None, error_message).

        *token* is ignored; authentication is via API key header.
        """
        record = None
        error_message = ''
        headers, err = self._get_census_request_headers()
        if not headers:
            return record, err
        try:
            resp = requests.get(
                '%s%s/%s' % (url, _ENDPOINT_PARTNERS, remote_id),
                headers=headers)
            if resp.status_code == 200:
                record = json.loads(resp.text)
            else:
                error_message = resp.text
        except Exception as e:
            error_message = _('Telecontrol Error: could not fetch partner %s. '
                              '%s') % (remote_id, _safe_str(e))
        return record, error_message

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    @api.model
    def _map_batchline_census_partner_vals(self, remote):
        """Convert a remote IrriWEB *irrigator* dict to Odoo field values.

        The IrriWEB tax-ID field (``nif``) is stored without the country prefix,
        so we prepend 'ES' to build a proper ``vat`` value.
        """
        def _clean(value):
            if isinstance(value, basestring):
                return value.strip()
            return value or ''

        tax_id_raw = _clean(remote.get('nif') or '')
        vat = ('ES' + tax_id_raw) if tax_id_raw and tax_id_raw != '-' else False

        firstname = _clean(remote.get('nombre') or '')
        lastname = _clean(remote.get('apellido1') or '')
        lastname2 = _clean(remote.get('apellido2') or '')

        # partner_firstname raises EmptyNamesError if all name fields are
        # empty. Fall back to the partner_code so the record can be created.
        partner_code = remote.get('identificador')
        if not firstname and not lastname and not lastname2:
            lastname = u'Irrigator %s' % partner_code

        return {
            'partner_code': partner_code,
            'id_irriweb': int(partner_code) if partner_code else 0,
            'firstname': firstname,
            'lastname': lastname,
            'lastname2': lastname2,
            'vat': vat,
            'email': _clean(remote.get('email') or '') or False,
            'street': _clean(remote.get('direccion') or '') or False,
            'city': _clean(remote.get('poblacion') or '') or False,
            'zip': _clean(remote.get('codPostal') or '') or False,
            'phone': _clean(remote.get('telefono') or '') or False,
        }

    # ------------------------------------------------------------------
    # Upsert single record
    # ------------------------------------------------------------------

    # Fields compared when deciding whether an existing partner needs updating.
    # Avoids unnecessary write() calls when IrriWEB data has not changed.
    _CENSUS_COMPARE_FIELDS = [
        'partner_code', 'firstname', 'lastname', 'lastname2',
        'vat', 'email', 'street', 'city', 'zip', 'phone',
    ]

    @api.model
    def _upsert_batchline_census_partner(self, vals, partner_by_code,
                                         warn_sink=None):
        """Create or update a ``res.partner`` from IrriWEB values.

        Uses *partner_code* as the unique match key; *partner_by_code* is a
        pre-loaded ``{partner_code: record}`` dict. Appends VAT-fallback
        warnings to *warn_sink* when provided.

        Returns ``True`` if a new record was created, ``False`` otherwise.
        Raises on unexpected ORM error.
        """
        partner_code = vals.get('partner_code')
        # Skip records with no code or non-positive codes: the wua.partner
        # constraint _check_partner_code requires partner_code > 0.
        if not partner_code or partner_code <= 0:
            return False

        existing = partner_by_code.get(partner_code)
        # Bypass outbound telecontrol hooks while writing.
        self.__class__._in_create_or_synchro = True
        try:
            if existing:
                # Compare fields; update only what changed.
                changed_vals = {}
                for field in self._CENSUS_COMPARE_FIELDS:
                    if field == 'partner_code':
                        continue
                    if field not in vals:
                        continue
                    new_val = vals[field] or False
                    old_val = getattr(existing, field, False) or False
                    if new_val != old_val:
                        changed_vals[field] = vals[field]
                if changed_vals:
                    self._write_with_vat_fallback(
                        existing, changed_vals, warn_sink=warn_sink)
                return False
            else:
                new_partner = self._create_with_vat_fallback(
                    vals, warn_sink=warn_sink)
                if new_partner:
                    partner_by_code[partner_code] = new_partner
                return True
        finally:
            self.__class__._in_create_or_synchro = False

    @api.model
    def _census_ctx(self):
        """Return a context dict that disables tracking and chatter noise."""
        return {
            'wua': '1',
            'tracking_disable': True,
            'mail_notrack': True,
            'no_recompute': True,
        }

    @api.model
    def _create_with_vat_fallback(self, vals, warn_sink=None):
        """Create a WUA partner; retry without VAT if validation fails.
        Appends a warning to *warn_sink* when the fallback is triggered.
        Returns the newly created record.
        """
        ctx = self._census_ctx()
        try:
            with self.env.cr.savepoint():
                return self.with_context(**ctx).create(
                    dict(vals, is_wua_partner=True, from_irriweb_census=True))
        except (ValidationError, UserError):
            if vals.get('vat'):
                msg = _(
                    'Duplicate or invalid VAT %s for partner_code %s '
                    '\u2014 created without VAT.') % (
                        vals['vat'], vals.get('partner_code'))
                _logger.warning(u'Batchline census sync: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(msg)
                vals_no_vat = dict(vals, vat=False)
                return self.with_context(**ctx).create(
                    dict(vals_no_vat, is_wua_partner=True,
                         from_irriweb_census=True))
            else:
                raise

    @api.model
    def _write_with_vat_fallback(self, partner, vals, warn_sink=None):
        """Write changed vals to an existing partner.

        If VAT validation fails, retries without the VAT field so the
        partner is updated rather than the whole record failing.

        *warn_sink* works the same as in ``_create_with_vat_fallback``.
        """
        ctx = self._census_ctx()
        try:
            with self.env.cr.savepoint():
                partner.with_context(**ctx).write(vals)
        except (ValidationError, UserError):
            if vals.get('vat'):
                msg = _(
                    'Duplicate or invalid VAT %s for partner_code %s '
                    '\u2014 updated without VAT.') % (
                        vals['vat'], partner.partner_code)
                _logger.warning(u'Batchline census sync: %s', msg)
                if warn_sink is not None:
                    warn_sink.append(msg)
                vals_no_vat = dict(vals, vat=False)
                partner.with_context(**ctx).write(vals_no_vat)
            else:
                raise

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    @api.model
    def action_census_sync_batchline_cron(self):
        """Cron entry point — called by ir.cron."""
        _logger.info('Batchline census sync: cron started')
        try:
            self._run_census_sync_batchline(trigger='cron')
        except Exception as e:
            _logger.error(
                'Batchline census sync: cron failed. %s', _safe_str(e))

    @api.multi
    def action_census_sync_batchline_manual(self):
        """Manual trigger from the configuration form.

        Returns an act_window action opening the created sync log.
        """
        log = self._run_census_sync_batchline(trigger='manual')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Census Sync Log'),
            'res_model': 'wua.census.sync.log',
            'res_id': log.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def action_census_sync_single_partner_batchline(self, remote_id):
        """Sync a single partner by its IrriWEB *identificador*.

        Returns a dict with counts: ``{'created': int, 'skipped': int,
        'errors': int}``.
        """
        url, _header, _value = self._get_census_connection_params()
        if not url:
            raise UserError(_(
                'Census API URL not configured '
                '(url_census_rest_batchline).'))

        remote, err = self.fetch_single_partner_from_batchline(
            url, None, remote_id)
        if err or not remote:
            raise UserError(_(
                'Batchline census sync: error fetching partner %s. %s')
                % (remote_id, err))

        vals = self._map_batchline_census_partner_vals(remote)
        partner_code = vals.get('partner_code')
        partner_by_code = {}
        if partner_code and partner_code > 0:
            existing = self.with_context(active_test=False).search(
                [('partner_code', '=', partner_code)], limit=1)
            if existing:
                partner_by_code[partner_code] = existing
        is_new = self._upsert_batchline_census_partner(vals, partner_by_code)
        created = 1 if is_new else 0
        skipped = 0 if is_new else 1
        return {'created': created, 'skipped': skipped, 'errors': 0}

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    @api.model
    def _run_census_sync_batchline(self, trigger='manual'):
        """Fetch the full partner census from IrriWEB and sync into Odoo.

        * Guard against concurrent runs.
        * Commits every ``_BATCH_SIZE`` records so progress survives
          a mid-run crash.
        * All warnings/errors are stored in ``wua.census.sync.log.line``.
        * Returns the ``wua.census.sync.log`` record.
        """
        SyncLog = self.env['wua.census.sync.log']

        # Guard: abort if another sync is already running
        running = SyncLog.search([('state', '=', 'running')], limit=1)
        if running:
            raise UserError(_(
                'A census sync is already running (log: %s). '
                'Please wait for it to finish.') % running.name)

        log = SyncLog.create({
            'date_start': fields.Datetime.now(),
            'trigger': trigger,
            'state': 'running',
        })
        # Commit so the log is visible even if the fetch fails
        self.env.cr.commit()

        try:
            result_partners = self._sync_partners_census_batchline(log)
            result_parcels = self.env['wua.parcel'].\
                action_census_sync_parcels_batchline(log=log)

            total_errors = (result_partners.get('errors', 0) +
                            result_parcels.get('errors', 0))
            total_warnings = (result_partners.get('warnings', 0) +
                              result_parcels.get('warnings', 0))
            if total_errors > 0:
                state = 'partial'
            else:
                state = 'success'
            summary = _(
                'Partners: created=%(p_created)d, skipped=%(p_skipped)d, '
                'warnings=%(p_warn)d, errors=%(p_errors)d\n'
                'Parcels:  created=%(f_created)d, skipped=%(f_skipped)d, '
                'warnings=%(f_warn)d [parcel=%(f_warn_parcel)d, '
                'partnerlink=%(f_warn_partnerlink)d], '
                'tomas=%(f_tomas)d, errors=%(f_errors)d'
            ) % {
                'p_created': result_partners.get('created', 0),
                'p_skipped': result_partners.get('skipped', 0),
                'p_warn': result_partners.get('warnings', 0),
                'p_errors': result_partners.get('errors', 0),
                'f_created': result_parcels.get('created', 0),
                'f_skipped': result_parcels.get('skipped', 0),
                'f_warn': result_parcels.get('warnings', 0),
                'f_warn_parcel': result_parcels.get('warning_parcel', 0),
                'f_warn_partnerlink': result_parcels.get(
                    'warning_partnerlink', 0),
                'f_tomas': result_parcels.get('tomas', 0),
                'f_errors': result_parcels.get('errors', 0),
            }
            self._update_census_sync_log_safe(log.id, {
                'state': state,
                'date_end': fields.Datetime.now(),
                'summary': summary,
            })
        except Exception as e:
            _logger.error(
                'Batchline census sync: fatal error. %s', _safe_str(e))
            self._update_census_sync_log_safe(log.id, {
                'state': 'error',
                'date_end': fields.Datetime.now(),
                'summary': _safe_str(e),
            })

        return log

    # ------------------------------------------------------------------
    # Core sync: partners
    # ------------------------------------------------------------------

    @api.model
    def _sync_partners_census_batchline(self, log):
        """Fetch all partners from IrriWEB and upsert them into Odoo.

        Returns a dict with counts: ``{'created': int, 'skipped': int,
        'warnings': int, 'errors': int}``.
        """
        url, _header, _value = self._get_census_connection_params()
        if not url:
            msg = _('Census API URL not configured '
                    '(url_census_rest_batchline).')
            self._census_sync_log_line(
                log, _ENDPOINT_PARTNERS, '', msg, level='error')
            self.env.cr.commit()
            return {'created': 0, 'skipped': 0, 'warnings': 0, 'errors': 1}

        records, err = self.fetch_all_partners_from_batchline(url, None)
        if err:
            self._census_sync_log_line(
                log, _ENDPOINT_PARTNERS, '', err, level='error')
            self.env.cr.commit()
            return {'created': 0, 'skipped': 0, 'warnings': 0, 'errors': 1}

        total = len(records)
        created = 0
        skipped = 0
        warnings = 0
        errors = 0

        _logger.info(
            'Batchline census sync: %d partners to process', total)

        # Pre-load existing WUA partners for O(1) lookups.
        all_existing = self.with_context(active_test=False).search([
            ('is_wua_partner', '=', True),
            ('partner_code', '>', 0),
        ])
        partner_by_code = {p.partner_code: p for p in all_existing}
        _logger.info(
            'Batchline census sync: %d existing WUA partners pre-loaded',
            len(partner_by_code))

        for batch_start in range(0, total, _BATCH_SIZE):
            batch = records[batch_start:batch_start + _BATCH_SIZE]
            for remote in batch:
                remote_id = remote.get('identificador', '')
                try:
                    vals = self._map_batchline_census_partner_vals(remote)
                    warn_sink = []
                    with self.env.cr.savepoint():
                        is_new = self._upsert_batchline_census_partner(
                            vals, partner_by_code, warn_sink=warn_sink)
                    # Record-level warnings (e.g. created without VAT)
                    for w in warn_sink:
                        warnings += 1
                        self._census_sync_log_line(
                            log, _ENDPOINT_PARTNERS, remote_id, w,
                            level='warning_partner')
                    if is_new is False and vals.get('partner_code', 0) <= 0:
                        # invalid code — not an error, just skip silently
                        continue
                    if is_new:
                        created += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    msg = _safe_str(e)
                    _logger.error(
                        'Batchline census sync: error on partner %s. %s',
                        remote_id, msg)
                    self._census_sync_log_line(
                        log, _ENDPOINT_PARTNERS, remote_id, msg,
                        level='error')

            # Commit after every batch and flush the ORM cache
            self.env.cr.commit()
            self.invalidate_cache()

            batch_end = batch_start + len(batch)
            _logger.info(
                'Batchline census sync: %d / %d processed '
                '(created=%d, skipped=%d, warnings=%d, errors=%d)',
                batch_end, total, created, skipped, warnings, errors)
            self._update_census_sync_log_safe(log.id, {
                'summary': _('Processing partners: %d / %d') % (
                    batch_end, total),
            })

        _logger.info(
            'Batchline census sync finished: created=%d, skipped=%d, '
            'warnings=%d, errors=%d', created, skipped, warnings, errors)
        return {
            'created': created,
            'skipped': skipped,
            'warnings': warnings,
            'errors': errors,
        }

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    @api.model
    def _census_sync_log_line(self, log, endpoint, external_code, message,
                               level='warning'):
        """Append a line to the sync log (persisted at next commit)."""
        self.env['wua.census.sync.log.line'].create({
            'log_id': log.id,
            'endpoint': endpoint,
            'external_code': unicode(external_code) if external_code else '',
            'message': message,
            'level': level,
        })

    @api.model
    def _update_census_sync_log_safe(self, log_id, vals):
        """Update ``wua.census.sync.log`` fields using a separate cursor
        so the update is committed immediately without flushing the main
        transaction.
        """
        new_cr = self.pool.cursor()
        try:
            sets = []
            params = []
            for k, v in vals.items():
                sets.append('"%s" = %%s' % k)
                params.append(v)
            sets.append("write_date = (now() at time zone 'UTC')")
            params.append(log_id)
            new_cr.execute(
                "UPDATE wua_census_sync_log SET %s WHERE id = %%s"
                % ', '.join(sets),
                params)
            new_cr.commit()
        except Exception as e:
            _logger.error(
                'Batchline census sync: could not update log %s. %s',
                log_id, _safe_str(e))
            try:
                new_cr.rollback()
            except Exception:
                pass
        finally:
            new_cr.close()
