# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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

    has_pending_invoices = fields.Boolean(
        string="Has invoices to validate",
        compute="_compute_validate_progress",
        help="True when the invoice set still has draft/proforma invoices "
        "pending validation. Used to hide the validation button once every "
        "invoice is already validated.",
    )

    @api.depends("validate_total", "validate_in_progress")
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
    def action_calculate_invoiceset_queue(self):
        self.ensure_one()
        self._check_can_enqueue()
        self.write({"calculate_in_progress": True})
        self.with_delay(
            description=_("Calculate invoice set %s") % self.name,
        ).calculate_invoiceset_job()
        self.message_post(
            body=_("Invoice set calculation has been enqueued and will run "
                   "in the background. Follow its progress in the Job Queue."),
        )
        return True

    @api.multi
    def action_calculate_and_validate_invoiceset_queue(self):
        self.ensure_one()
        self._check_can_enqueue()
        self.write({"calculate_in_progress": True})
        self.with_delay(
            description=_("Calculate and validate invoice set %s")
            % self.name,
        ).calculate_and_validate_invoiceset_job()
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
        self._enqueue_validation_partitions()
        self.message_post(
            body=_("Invoice validation has been enqueued and will run in "
                   "the background. Follow the progress bar on this form."),
        )
        return True

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_invoiceset_job(self):
        self.ensure_one()
        try:
            self.calculate_invoiceset()
        finally:
            self._clear_calculate_in_progress()
        return True

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_and_validate_invoiceset_job(self):
        self.ensure_one()
        try:
            self.calculate_invoiceset()
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
            SELECT id
            FROM account_invoice
            WHERE invoiceset_id = %s
              AND state IN ('draft', 'proforma', 'proforma2')
            ORDER BY id
            """,
            (self.id,),
        )
        invoice_ids = [row[0] for row in self.env.cr.fetchall()]
        if not invoice_ids:
            return True
        partitions = self._split_in_partitions(
            invoice_ids, self._get_validate_partitions())
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
        validated = 0
        errors = 0
        for start in range(0, len(invoice_ids), chunk_size):
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
            # Commit each chunk as an independent transaction. Progress is
            # derived on read with a COUNT (see _compute_validate_progress),
            # so a worker never writes to the shared invoiceset row here and
            # therefore never takes a row lock the other workers must wait on.
            self.env.cr.commit()
        _logger.info(
            "[invoiceset %s] partition done: %s validated, %s errors.",
            self.name, validated, errors,
        )
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
            self.message_post(
                body=_("Invoice validation finished: %s invoices validated.")
                % self.validate_total)
        return True
