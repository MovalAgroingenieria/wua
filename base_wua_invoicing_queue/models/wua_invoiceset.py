# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class WuaInvoiceset(models.Model):
    _inherit = "wua.invoiceset"

    # Default number of parallel partitions used to validate the invoices of
    # a set when no system parameter overrides it. The real speed-up is
    # bounded by the number of queue_job workers the instance has running:
    # with a single worker the partitions execute one after another (no
    # speed-up). Override per database with the system parameter
    # 'base_wua_invoicing_queue.validate_partitions'.
    VALIDATE_PARTITIONS = 4

    # Chunk size inside each partition job: each chunk is an independent
    # transaction (commit per chunk) to keep locks and ORM cache small.
    VALIDATE_PARTITION_CHUNK = 100

    # Chunk size for the materialization step. Kept below
    # 'commit_every_n_invoices' so create_invoices never issues its own
    # internal commit in the middle of our chunk savepoint.
    MATERIALIZE_CHUNK = 50

    validate_in_progress = fields.Boolean(
        string="Validation in progress",
        default=False,
        copy=False,
    )

    calculate_in_progress = fields.Boolean(
        string="Calculation in progress",
        default=False,
        copy=False,
        help="True while the invoice-set generation job is running. The "
        "calculation is a single sequential process, so it is shown as a "
        "plain busy indicator rather than a percentage.",
    )

    active_plan_id = fields.Many2one(
        string="Active plan",
        comodel_name="wua.invoiceset.plan",
        copy=False,
    )

    calculate_phase = fields.Selection(
        string="Calculation phase",
        related="active_plan_id.phase",
        readonly=True,
    )

    calculate_total = fields.Integer(
        string="Invoices to create",
        related="active_plan_id.line_total",
        readonly=True,
    )

    calculate_done = fields.Integer(
        string="Invoices created",
        related="active_plan_id.line_done",
        readonly=True,
    )

    calculate_progress = fields.Float(
        string="Calculation progress",
        related="active_plan_id.progress",
        readonly=True,
    )

    validate_total = fields.Integer(
        string="Invoices to validate",
        default=0,
        copy=False,
    )

    validate_done = fields.Integer(
        string="Invoices validated",
        compute="_compute_validate_progress",
        help="Invoices already validated, derived on read from a COUNT so "
        "the parallel workers never write to this record (no row lock).",
    )

    validate_progress = fields.Float(
        string="Validation progress",
        compute="_compute_validate_progress",
        help="Percentage of invoices validated by the parallel jobs.",
    )

    validate_pending = fields.Integer(
        string="Invoices pending validation",
        compute="_compute_validate_progress",
        help="Number of draft/proforma invoices still pending validation.",
    )

    has_pending_invoices = fields.Boolean(
        string="Has invoices to validate",
        compute="_compute_validate_progress",
        help="True when the invoice set still has draft/proforma invoices "
        "pending validation. Used to hide the validation button once every "
        "invoice is already validated.",
    )

    def _compute_validate_progress(self):
        # Derive progress on read with a single COUNT instead of having the
        # workers UPDATE a shared counter. This removes the only row lock the
        # parallel partition jobs would otherwise take on this record: while
        # validating they touch ONLY their own invoices, never this row.
        for record in self:
            done = 0
            pending = 0
            if record.id:
                record.env.cr.execute(
                    """
                    SELECT
                        count(*) FILTER (
                            WHERE state NOT IN
                                ('draft', 'proforma', 'proforma2')),
                        count(*) FILTER (
                            WHERE state IN
                                ('draft', 'proforma', 'proforma2'))
                    FROM account_invoice
                    WHERE invoiceset_id = %s
                    """,
                    (record.id,),
                )
                row = record.env.cr.fetchone()
                done, pending = row[0], row[1]
            record.validate_pending = pending
            record.has_pending_invoices = pending > 0
            if record.validate_total and done > record.validate_total:
                done = record.validate_total
            record.validate_done = done
            if record.validate_total > 0:
                record.validate_progress = (
                    100.0 * done / record.validate_total)
            else:
                record.validate_progress = 0.0

    @api.model
    def _get_validate_partitions(self):
        """Number of parallel partitions, configurable per database via the
        system parameter 'base_wua_invoicing_queue.validate_partitions'.
        Falls back to VALIDATE_PARTITIONS when unset or invalid."""
        param = self.env["ir.config_parameter"].sudo().get_param(
            "base_wua_invoicing_queue.validate_partitions")
        try:
            value = int(param)
        except (TypeError, ValueError):
            value = self.VALIDATE_PARTITIONS
        if value < 1:
            value = self.VALIDATE_PARTITIONS
        return value

    @api.multi
    def _check_can_enqueue(self):
        self.ensure_one()
        if self.is_being_computed:
            raise UserError(_(
                "The invoice set is already being computed. Please wait."))
        if self.calculate_in_progress:
            raise UserError(_(
                "A calculation is already running for this invoice set."))
        if not self.configured_invoiceset:
            raise UserError(_(
                "The invoice set is not configured. Please configure it "
                "first."))
        if self.state == "generated":
            raise UserError(_(
                "The invoice set is already generated. Cancel it first if "
                "you want to recalculate."))
        return True

    @api.multi
    def _acquire_calculation_in_progress(self):
        """Atomically mark the invoice set as being calculated.

        This prevents double-clicks and multi-tab races from enqueuing more
        than one calculation job for the same invoice set.
        """
        self.ensure_one()
        self.env.cr.execute(
            """
            UPDATE wua_invoiceset
            SET calculate_in_progress = true
            WHERE id = %s
              AND calculate_in_progress = false
            RETURNING id
            """,
            (self.id,),
        )
        won = self.env.cr.fetchone()
        self.invalidate_cache(["calculate_in_progress"])
        if not won:
            raise UserError(_(
                "A calculation is already running for this invoice set."))
        return True

    @api.multi
    def action_calculate_invoiceset_queue(self):
        self.ensure_one()
        self._check_can_enqueue()
        self._acquire_calculation_in_progress()
        try:
            self.with_delay(
                description=_("Calculate invoice set %s") % self.name,
            ).compute_plan_job()
        except Exception:
            self._clear_calculate_in_progress()
            raise
        self.message_post(
            body=_("Invoice set calculation has been enqueued and will run "
                   "in the background. Follow its progress in the Job Queue."),
        )
        return True

    @api.multi
    def action_calculate_and_validate_invoiceset_queue(self):
        self.ensure_one()
        self._check_can_enqueue()
        self._acquire_calculation_in_progress()
        try:
            self.with_delay(
                description=_("Calculate and validate invoice set %s")
                % self.name,
            ).compute_plan_job(validate_after=True)
        except Exception:
            self._clear_calculate_in_progress()
            raise
        self.message_post(
            body=_("Invoice set calculation and validation have been "
                   "enqueued and will run in the background. Follow the "
                   "validation progress bar on this form."),
        )
        return True

    @api.multi
    def action_validate_invoiceset_queue(self):
        self.ensure_one()
        if self.state != "generated":
            raise UserError(_(
                "The invoice set must be generated before validating its "
                "invoices."))
        if self.validate_in_progress:
            raise UserError(_(
                "A validation is already running for this invoice set."))
        self._compute_validate_progress()
        if self.validate_pending <= 0:
            raise UserError(_(
                "All invoices of this set are already validated."))
        self._enqueue_validation_partitions()
        self.message_post(
            body=_("Invoice validation has been enqueued and will run in "
                   "the background. Follow the progress bar on this form."),
        )
        return True

    @api.multi
    def calculate_invoiceset(self):
        if not self.env.context.get("queue_background_calculation"):
            for record in self:
                if record.calculate_in_progress:
                    raise UserError(_(
                        "A background calculation is already running for "
                        "this invoice set. Please wait until it finishes."
                    ))
        return super(WuaInvoiceset, self).calculate_invoiceset()

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_invoiceset_job(self):
        self.ensure_one()
        try:
            self.with_context(
                queue_background_calculation=True,
            ).calculate_invoiceset()
        finally:
            self._clear_calculate_in_progress()
        return True

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_and_validate_invoiceset_job(self):
        self.ensure_one()
        try:
            self.with_context(
                queue_background_calculation=True,
            ).calculate_invoiceset()
        finally:
            self._clear_calculate_in_progress()
        self._enqueue_validation_partitions()
        return True

    @api.multi
    def _clear_calculate_in_progress(self):
        """Clear the calculation busy flag with a direct SQL UPDATE so it is
        committed even if the surrounding transaction is later rolled back."""
        self.ensure_one()
        self.env.cr.execute(
            """
            UPDATE wua_invoiceset
            SET calculate_in_progress = false
            WHERE id = %s
            """,
            (self.id,),
        )
        self.invalidate_cache(["calculate_in_progress"])
        return True

    @api.multi
    def _create_plan(self, validate_after=False):
        self.ensure_one()
        plan = self.env['wua.invoiceset.plan'].create({
            'invoiceset_id': self.id,
            'state': 'computing',
            'phase': 'select_items',
            'validate_after': validate_after,
            'date_start': fields.Datetime.now(),
            'job_uuid': self.env.context.get('job_uuid') or False,
        })
        self.active_plan_id = plan
        self.env.cr.commit()
        return plan

    @api.multi
    def _set_plan_phase(self, plan, phase, state=None):
        self.ensure_one()
        values = {'phase': phase}
        if state:
            values['state'] = state
        plan.write(values)
        self.env.cr.commit()
        return True

    @api.multi
    def _mark_plan_failed(self, plan):
        self.ensure_one()
        self.env.cr.execute(
            "UPDATE wua_invoiceset_plan SET state = 'failed' "
            "WHERE id = %s",
            (plan.id,),
        )
        self.env.cr.commit()
        plan.invalidate_cache(['state'])
        return True

    @api.multi
    def _get_materialize_chunk(self):
        self.ensure_one()
        commit_every = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'commit_every_n_invoices')
        try:
            commit_every = int(commit_every)
        except (TypeError, ValueError):
            commit_every = self.COMMIT_EVERY_N_INVOICES
        if commit_every < 2:
            commit_every = self.COMMIT_EVERY_N_INVOICES
        chunk = self.MATERIALIZE_CHUNK
        if chunk >= commit_every:
            chunk = commit_every - 1
        if chunk < 1:
            chunk = 1
        return chunk

    @api.multi
    def _post_job_message(self, body, commit_now=False):
        """Post an informative message on the running queue.job chatter so the
        operator can follow batch progress from the Job Queue view."""
        self.ensure_one()
        job_uuid = self.env.context.get('job_uuid')
        if job_uuid:
            job_rec = self.env['queue.job'].search(
                [('uuid', '=', job_uuid)], limit=1)
            if job_rec:
                job_rec.message_post(body=body)
                if commit_now:
                    self.env.cr.commit()
        return True

    @api.multi
    def _notify_finished(self, ok, summary):
        self.ensure_one()
        self._post_job_message(summary)
        user = self.env.user
        self.message_post(
            body=summary,
            partner_ids=[user.partner_id.id],
            subtype='mail.mt_comment',
        )
        self.env['bus.bus'].sendone(
            ('wua_invoiceset_notif', user.id),
            {'title': _('Invoice set %s') % self.name,
             'message': summary,
             'sticky': False},
        )
        return True

    @api.multi
    @job(default_channel='root.base_wua_invoicing_queue')
    def compute_plan_job(self, validate_after=False):
        self.ensure_one()
        plan = self._create_plan(validate_after=validate_after)
        try:
            self.with_context(
                queue_background_calculation=True,
            )._build_plan(plan)
        except Exception:
            # Job-level failure boundary (NOT a per-item loop): recover the
            # cursor so we can persist the failed state and notify.
            self.env.cr.rollback()
            self._mark_plan_failed(plan)
            self._clear_calculate_in_progress()
            self._notify_finished(False, _(
                'Invoice set %s calculation FAILED. '
                'Check the job queue.') % self.name)
            raise
        self.with_delay(
            description=_('Materialize invoice set %s') % self.name,
        ).materialize_plan_job(plan.id)
        return True

    @api.multi
    def _build_plan(self, plan):
        self.ensure_one()
        self._set_plan_phase(plan, 'select_items')
        invoice_items = self.select_invoice_items(self)
        self._set_plan_phase(plan, 'calc_details')
        invoice_details = self.calculate_invoice_details(invoice_items)
        self._set_plan_phase(plan, 'grouping')
        invoices_data = self.group_invoice_details(invoice_details)
        plan_line_model = self.env['wua.invoiceset.plan.line']
        sequence = 10
        for invoice_data in invoices_data:
            plan_line_model.create({
                'plan_id': plan.id,
                'partner_id': invoice_data.get('partner_id'),
                'invoice_data_json': json.dumps(invoice_data),
                'sequence': sequence,
                'state': 'draft',
            })
            sequence += 10
        plan.write({
            'details_json': json.dumps(invoice_details),
            'line_total': len(invoices_data),
            'state': 'planned',
            'date_planned': fields.Datetime.now(),
        })
        self.env.cr.commit()
        return True

    @api.multi
    @job(default_channel='root.base_wua_invoicing_queue')
    def materialize_plan_job(self, plan_id):
        self.ensure_one()
        plan = self.env['wua.invoiceset.plan'].browse(plan_id)
        try:
            self._materialize_plan(plan)
        except Exception:
            self.env.cr.rollback()
            self._mark_plan_failed(plan)
            self._clear_calculate_in_progress()
            self._notify_finished(False, _(
                'Invoice set %s materialization FAILED. '
                'Check the job queue.') % self.name)
            raise
        return True

    @api.multi
    def _materialize_plan(self, plan):
        self.ensure_one()
        product_data = self.get_product_data(self.line_ids)
        self._set_plan_phase(plan, 'creating_invoices',
                             state='materializing')
        chunk_size = self._get_materialize_chunk()
        pending = plan.line_ids.filtered(
            lambda l: l.state == 'draft').sorted(key=lambda l: l.sequence)
        for start in range(0, len(pending), chunk_size):
            chunk = pending[start:start + chunk_size]
            self._materialize_chunk(chunk, product_data)
            self.env.cr.commit()
        remaining = plan.line_ids.filtered(lambda l: l.state == 'draft')
        if not remaining:
            self._finalize_plan(plan)
        self._clear_calculate_in_progress()
        self._notify_finished(True, _(
            'Invoice set %s calculated: %s invoices created.') % (
            self.name, plan.line_total))
        if plan.validate_after and not remaining:
            self._enqueue_validation_partitions()
        return True

    @api.multi
    def _materialize_chunk(self, chunk, product_data):
        self.ensure_one()
        invoices_data = [
            json.loads(line.invoice_data_json) for line in chunk]
        self.env.cr.execute(
            "SELECT COALESCE(MAX(id), 0) FROM account_invoice")
        before_max = self.env.cr.fetchone()[0]
        try:
            with self.env.cr.savepoint():
                self.create_invoices(invoices_data, self, product_data)
            self.env.cr.execute(
                "SELECT id FROM account_invoice "
                "WHERE invoiceset_id = %s AND id > %s ORDER BY id",
                (self.id, before_max),
            )
            new_ids = [row[0] for row in self.env.cr.fetchall()]
            for line, invoice_id in zip(chunk, new_ids):
                line.write({'invoice_id': invoice_id, 'state': 'done'})
            # If counts differ, still mark remaining lines done so retries do
            # not recreate them (idempotency relies on 'state', invoice_id is
            # only informative).
            for line in chunk[len(new_ids):]:
                line.write({'state': 'done'})
        except Exception as chunk_error:
            _logger.warning(
                '[invoiceset %s] materialize chunk failed (%s); '
                'retrying line by line.', self.name, chunk_error)
            self._materialize_chunk_one_by_one(chunk, product_data)
        return True

    @api.multi
    def _materialize_chunk_one_by_one(self, chunk, product_data):
        self.ensure_one()
        for line in chunk:
            invoice_data = json.loads(line.invoice_data_json)
            self.env.cr.execute(
                "SELECT COALESCE(MAX(id), 0) FROM account_invoice")
            before_max = self.env.cr.fetchone()[0]
            try:
                with self.env.cr.savepoint():
                    self.create_invoices(
                        [invoice_data], self, product_data)
                self.env.cr.execute(
                    "SELECT id FROM account_invoice "
                    "WHERE invoiceset_id = %s AND id > %s ORDER BY id",
                    (self.id, before_max),
                )
                new_ids = [row[0] for row in self.env.cr.fetchall()]
                values = {'state': 'done'}
                if new_ids:
                    values['invoice_id'] = new_ids[0]
                line.write(values)
            except Exception as line_error:
                line.write({
                    'state': 'error',
                    'error_info': str(line_error),
                })
                _logger.warning(
                    '[invoiceset %s] failed to create invoice for '
                    'partner %s: %s',
                    self.name, line.partner_id.id, line_error)
        return True

    @api.multi
    def _finalize_plan(self, plan):
        self.ensure_one()
        self._set_plan_phase(plan, 'finalizing')
        invoice_details = json.loads(plan.details_json or '[]')
        total_quantities = self.get_total_product_quantities(invoice_details)
        self.update_invoiceset_quantities(self, total_quantities)
        amounts = self.update_invoiceset_amounts(self)
        done_lines = plan.line_ids.filtered(lambda l: l.state == 'done')
        self.write({
            'amount_untaxed': amounts['amount_untaxed'],
            'amount_tax': amounts['amount_tax'],
            'amount_total': amounts['amount_total'],
            'number_of_invoices': len(done_lines),
            'state': 'generated',
        })
        self.after_calculate_invoiceset(self)
        plan.write({
            'state': 'done',
            'date_done': fields.Datetime.now(),
        })
        self.env.cr.commit()
        return True

    @api.multi
    def _enqueue_validation_partitions(self):
        """Split the pending invoices into disjoint partitions and enqueue a
        validation job per partition.

        Concurrency notes:
        - Each partition validates a *disjoint* set of invoice ids, so no two
          jobs ever write the same account.invoice / account.move /
          account.move.line row.
        - Partition jobs update the shared progress counters with atomic SQL
          UPDATEs only (never a full ORM write on the wua.invoiceset record),
          so concurrent workers do not serialise on that row.
        - The real point of serialisation is the journal sequence requested by
          account.move.post(): PostgreSQL row-locks it, so workers wait there
          but never corrupt data. This also means invoice numbering follows
          the validation order, not the invoice id order.
        """
        self.ensure_one()
        self.env.cr.execute(
            """
            SELECT id, journal_id
            FROM account_invoice
            WHERE invoiceset_id = %s
              AND state IN ('draft', 'proforma', 'proforma2')
            ORDER BY journal_id, id
            """,
            (self.id,),
        )
        invoice_rows = self.env.cr.fetchall()
        invoice_ids = [row[0] for row in invoice_rows]
        if not invoice_ids:
            return True
        partitions = self._split_in_partitions_by_journal(
            invoice_rows, self._get_validate_partitions())
        # Mark the validation as running and record the total. No per-partition
        # counter is kept: completion is decided by a COUNT of the invoices
        # that are still pending (see _maybe_finish_validation), which is
        # idempotent under retries and restart-requeue.
        self.write({
            "validate_in_progress": True,
            "validate_total": len(invoice_ids),
        })
        for index, partition_ids in enumerate(partitions):
            self.with_delay(
                description=_("Validate invoice set %s (partition %s/%s)")
                % (self.name, index + 1, len(partitions)),
            ).validate_partition_job(partition_ids)
        return True

    @api.model
    def _split_in_partitions_by_journal(self, invoice_rows, partitions):
        """Split pending invoices into partitions without mixing journals.

        Posting invoices of the same journal competes for the same sequence
        row lock. Keeping one journal in a single partition avoids workers
        fighting each other, while different journals can still run in
        parallel.
        """
        if not invoice_rows:
            return []
        journal_groups = {}
        journal_order = []
        for invoice_id, journal_id in invoice_rows:
            if journal_id not in journal_groups:
                journal_groups[journal_id] = []
                journal_order.append(journal_id)
            journal_groups[journal_id].append(invoice_id)
        if len(journal_groups) == 1:
            only_group = journal_groups[journal_order[0]]
            return [only_group]
        effective_partitions = max(1, min(partitions, len(journal_groups)))
        buckets = []
        for _index in range(effective_partitions):
            buckets.append([])
        for journal_id in journal_order:
            target_bucket = min(
                range(effective_partitions),
                key=lambda bucket_index: len(buckets[bucket_index]),
            )
            buckets[target_bucket].extend(journal_groups[journal_id])
        return [bucket for bucket in buckets if bucket]

    @api.model
    def _split_in_partitions(self, ids, partitions):
        partitions = max(1, min(partitions, len(ids)))
        buckets = [[] for _ in range(partitions)]
        # Round-robin keeps every bucket balanced regardless of id gaps.
        for position, record_id in enumerate(ids):
            buckets[position % partitions].append(record_id)
        return [bucket for bucket in buckets if bucket]

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def validate_partition_job(self, invoice_ids):
        """Validate a disjoint partition of invoices in committed chunks.

        Idempotent and resumable: each chunk is re-filtered (fresh SQL read,
        not the ORM cache) to the invoices that are still pending. Invoices
        already validated in a previous run are skipped, so:
          - a queue_job retry does not reprocess them nor raise on the
            already-open ones;
          - after an instance restart, re-queuing the job resumes exactly
            where it left off (the invoice ``state`` is the only checkpoint
            needed, so nothing extra has to be persisted).

        Each invoice goes through the standard ``action_invoice_open`` so all
        per-invoice logic still runs (stored computed fields, analytic lines
        and the legally required Verifacti submission). The speed-up comes
        purely from running several partition jobs in parallel, NOT from
        skipping per-invoice work; the result is identical to a normal
        one-by-one validation.
        """
        self.ensure_one()
        invoice_model = self.env["account.invoice"]
        pending_states = ("draft", "proforma", "proforma2")
        chunk_size = self.VALIDATE_PARTITION_CHUNK
        total = len(invoice_ids)
        total_chunks = (total + chunk_size - 1) // chunk_size
        validated = 0
        errors = 0
        self._post_job_message(_(
            "Validating a partition of %s invoices in %s chunks of %s.")
            % (total, total_chunks, chunk_size), commit_now=True)
        for chunk_index, start in enumerate(
                range(0, total, chunk_size), start=1):
            chunk_ids = invoice_ids[start:start + chunk_size]
            # Re-read the still-pending ids of this chunk from the database so
            # the job is idempotent across retries and restarts.
            self.env.cr.execute(
                """
                SELECT id
                FROM account_invoice
                WHERE id IN %s
                  AND state IN %s
                """,
                (tuple(chunk_ids), pending_states),
            )
            pending_ids = [row[0] for row in self.env.cr.fetchall()]
            if not pending_ids:
                continue
            chunk = invoice_model.browse(pending_ids)
            chunk_ok = 0
            try:
                with self.env.cr.savepoint():
                    chunk.action_invoice_open()
                chunk_ok = len(pending_ids)
            except Exception as chunk_error:
                _logger.warning(
                    "[invoiceset %s] partition chunk failed (%s); "
                    "retrying invoice by invoice.",
                    self.name, chunk_error,
                )
                for invoice in chunk:
                    try:
                        with self.env.cr.savepoint():
                            invoice.action_invoice_open()
                        chunk_ok += 1
                    except Exception as invoice_error:
                        errors += 1
                        _logger.warning(
                            "[invoiceset %s] failed to validate invoice "
                            "%s: %s",
                            self.name, invoice.id, invoice_error,
                        )
            validated += chunk_ok
            self._post_job_message(_(
                "Chunk %s/%s done: %s/%s invoices validated in this "
                "partition (%s errors).")
                % (chunk_index, total_chunks, validated, total, errors))
            # Commit each chunk as an independent transaction. Progress is
            # derived on read with a COUNT (see _compute_validate_progress),
            # so a worker never writes to the shared invoiceset row here and
            # therefore never takes a row lock the other workers must wait on.
            self.env.cr.commit()
        _logger.info(
            "[invoiceset %s] partition done: %s validated, %s errors.",
            self.name, validated, errors,
        )
        self._post_job_message(_(
            "Partition finished: %s invoices validated, %s errors.")
            % (validated, errors), commit_now=True)
        self._maybe_finish_validation()
        return True

    @api.multi
    def _maybe_finish_validation(self):
        """Mark the validation as finished when no pending invoice is left.

        Idempotent by design: every partition worker that finishes runs the
        same COUNT, but only the worker whose UPDATE actually flips
        validate_in_progress from true to false (atomic, RETURNING) posts the
        completion message. Concurrent workers that see the flag already
        false get no row back and stay silent, so the chatter never gets
        duplicate messages."""
        self.ensure_one()
        self.env.cr.execute(
            """
            SELECT count(*)
            FROM account_invoice
            WHERE invoiceset_id = %s
              AND state IN ('draft', 'proforma', 'proforma2')
            """,
            (self.id,),
        )
        remaining = self.env.cr.fetchone()[0]
        if remaining != 0:
            return True
        self.env.cr.execute(
            """
            UPDATE wua_invoiceset
            SET validate_in_progress = false
            WHERE id = %s
              AND validate_in_progress = true
            RETURNING id
            """,
            (self.id,),
        )
        won = self.env.cr.fetchone()
        self.env.cr.commit()
        self.invalidate_cache(["validate_in_progress"])
        if won:
            # Only the worker that flipped the flag reaches here, so the
            # completion message is posted exactly once.
            self._notify_finished(True, _(
                "Invoice validation finished: %s invoices validated.")
                % self.validate_total)
        return True
