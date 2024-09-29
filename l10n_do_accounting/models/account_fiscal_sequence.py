# © 2019 José López <jlopez@indexa.do>
# © 2019 Raul Ovalle <rovalle@guavana.com>

import pytz
import re
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


def get_l10n_do_datetime():
    """
    Multipurpose Dominican Republic local datetime
    """

    # *-*-*-*-*- Remove this comment *-*-*-*-*-*
    # Because an user can use a distinct timezone,
    # this method ensure that DR localtime stuff like
    # auto expire Fiscal Sequence by its date works,
    # no matter server/client date.

    date_now = datetime.now()
    return pytz.timezone("America/Santo_Domingo").localize(date_now)


class AccountFiscalSequence(models.Model):
    _name = "account.fiscal.sequence"
    _description = "Account Fiscal Sequence"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Authorization number",
        required=True,
        tracking=True,
    )
    expiration_date = fields.Date(
        required=True,
        tracking=True,
        default=datetime.strptime(
            str(int(str(fields.Date.today())[0:4]) + 1) + "-12-31", "%Y-%m-%d"
        ).date(),
    )
    fiscal_type_id = fields.Many2one(
        string='Fiscal type',
        comodel_name="account.fiscal.type",
        required=True,
        tracking=True,
    )
    type = fields.Selection(
        related="fiscal_type_id.type",
        store=True,
    )
    sequence_start = fields.Integer(
        required=True,
        tracking=True,
        default=1,
        copy=False,
    )
    sequence_end = fields.Integer(
        required=True,
        tracking=True,
        default=1,
        copy=False,
    )
    sequence_remaining = fields.Integer(
        string="Remaining",
        compute="_compute_sequence_remaining",
    )
    sequence_id = fields.Many2one(
        "ir.sequence", string="Internal Sequence", copy=False,
    )
    warning_gap = fields.Integer(compute="_compute_warning_gap",)
    remaining_percentage = fields.Float(
        default=35,
        required=True,
        help="Fiscal Sequence remaining percentage to reach to start "
        "warning notifications.",
    )
    number_next_actual = fields.Integer(
        string="Next Number",
        help="Next number of this sequence",
        related="sequence_id.number_next_actual",
    )
    next_fiscal_number = fields.Char(compute="_compute_next_fiscal_number",)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("queue", "Queue"),
            ("active", "Active"),
            ("depleted", "Depleted"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
        copy=False,
    )
    can_be_queue = fields.Boolean(compute="_compute_can_be_queue",)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        tracking=True,
    )

    @api.depends("state")
    def _compute_can_be_queue(self):
        for rec in self:
            rec.can_be_queue = (
                bool(
                    2
                    > self.search_count(
                        [
                            ("state", "in", ("active", "queue")),
                            ("fiscal_type_id", "=", rec.fiscal_type_id.id),
                            ("company_id", "=", rec.company_id.id),
                        ]
                    )
                    > 0
                )
                if rec.state == "draft"
                else False
            )

    @api.depends("remaining_percentage")
    def _compute_warning_gap(self):
        for rec in self:
            rec.warning_gap = (rec.sequence_end - (rec.sequence_start - 1)) * (
                rec.remaining_percentage / 100
            )

    @api.depends("sequence_end", "sequence_id.number_next")
    def _compute_sequence_remaining(self):
        for rec in self:
            rec.sequence_remaining = \
                (rec.sequence_end - rec.sequence_id.number_next_actual + 1) if rec.sequence_id else 0

    @api.depends("fiscal_type_id.prefix", "sequence_id.padding", "sequence_id.number_next_actual")
    def _compute_next_fiscal_number(self):
        for seq in self:
            seq.next_fiscal_number = "%s%s" % (
                seq.fiscal_type_id.prefix,
                str(seq.sequence_id.number_next_actual).zfill(seq.sequence_id.padding),
            )

    @api.onchange("fiscal_type_id")
    def _onchange_fiscal_type_id(self):
        """
        Compute draft Fiscal Sequence default sequence_start
        """
        if self.fiscal_type_id and self.state == "draft":
            # Last active or depleted Fiscal Sequence
            fs_id = self.search(
                [
                    ("fiscal_type_id", "=", self.fiscal_type_id.id),
                    ("state", "in", ("depleted", "active")),
                    ("company_id", "=", self.company_id.id),
                ],
                order="sequence_end desc",
                limit=1,
            )
            self.sequence_start = fs_id.sequence_end + 1 if fs_id else 1

    @api.constrains("fiscal_type_id", "state")
    def _validate_unique_active_type(self):
        """
        Validate an active sequence type uniqueness
        """
        domain = [
            ("state", "=", "active"),
            ("fiscal_type_id", "=", self.fiscal_type_id.id),
            ("company_id", "=", self.company_id.id),
        ]
        if self.search_count(domain) > 1:
            raise ValidationError(_("Another sequence is active for this type."))

    @api.constrains("sequence_start", "sequence_end", "state", "fiscal_type_id", "company_id")
    def _validate_sequence_range(self):
        for rec in self.filtered(lambda s: s.state != "cancelled"):
            if any(
                [True for value in [rec.sequence_start, rec.sequence_end] if value <= 0]
            ):
                raise ValidationError(_("Sequence values must be greater than zero."))
            if rec.sequence_start >= rec.sequence_end:
                raise ValidationError(
                    _("End sequence must be greater than start sequence.")
                )
            domain = [
                ("sequence_start", ">=", rec.sequence_start),
                ("sequence_end", "<=", rec.sequence_end),
                ("fiscal_type_id", "=", rec.fiscal_type_id.id),
                ("state", "in", ("active", "queue")),
                ("company_id", "=", rec.company_id.id),
            ]
            if self.search_count(domain) > 1:
                raise ValidationError(
                    _("You cannot use another Fiscal Sequence range.")
                )

    def unlink(self):
        for rec in self:
            if rec.sequence_id:
                rec.sequence_id.sudo().unlink()
        return super(AccountFiscalSequence, self).unlink()

    def copy(self, default=None):
        if default != 'etc':
            raise UserError(_("You cannot duplicate a Fiscal Sequence."))
        return super(AccountFiscalSequence, self).copy(default=default)

    def name_get(self):
        result = []
        for sequence in self:
            result.append(
                (sequence.id, "%s - %s" % (sequence.name, sequence.fiscal_type_id.name))
            )
        return result

    def action_view_sequence(self):
        self.ensure_one()
        sequence_id = self.sequence_id
        action = self.env.ref("base.ir_sequence_form").read()[0]
        if sequence_id:
            action["views"] = [(self.env.ref("base.sequence_view").id, "form")]
            action["res_id"] = sequence_id.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def action_confirm(self):
        self.ensure_one()
        msg = _(
            "Are you sure want to confirm this Fiscal Sequence? "
            "Once you confirm this Fiscal Sequence cannot be edited."
        )
        action = self.sudo().env.ref(
            "l10n_do_accounting.account_fiscal_sequence_validate_wizard_action"
        ).read()[0]
        action["context"] = {
            "default_name": msg,
            "default_fiscal_sequence_id": self.id,
            "action": "confirm",
        }
        return action

    def _action_confirm(self):
        for rec in self:

            # Use DR local time
            l10n_do_date = get_l10n_do_datetime().date()

            if l10n_do_date >= rec.expiration_date:
                rec.state = "expired"
            else:
                # Creates a new sequence of this Fiscal Sequence
                sequence_id = self.env["ir.sequence"].create(
                    {
                        "name": _("%s %s Sequence")
                        % (rec.fiscal_type_id.name, rec.name[-9:]),
                        "implementation": "standard",
                        "padding": rec.fiscal_type_id.padding,
                        "number_increment": 1,
                        "number_next_actual": rec.sequence_start,
                        "number_next": rec.sequence_start,
                        "use_date_range": False,
                        "company_id": rec.company_id.id,
                    }
                )
                rec.write(
                    {"state": "active", "sequence_id": sequence_id.id}
                )

    def action_cancel(self):
        self.ensure_one()
        msg = _(
            "Are you sure want to cancel this Fiscal Sequence? "
            "Once you cancel this Fiscal Sequence cannot be used."
        )
        action = self.env.ref(
            "l10n_do_accounting.account_fiscal_sequence_validate_wizard_action"
        ).read()[0]
        action["context"] = {
            "default_name": msg,
            "default_fiscal_sequence_id": self.id,
            "action": "cancel",
        }
        return action

    def _action_cancel(self):
        for rec in self:
            rec.state = "cancelled"
            if rec.sequence_id:
                # *-*-*-*-*- Remove this comment *-*-*-*-*-*
                # Preserve internal sequence just for audit purpose.
                rec.sequence_id.active = False

    def action_queue(self):
        for rec in self:
            rec.state = "queue"

    def _expire_sequences(self):
        """
        Function called from ir.cron that check all active sequence
        expiration_date and set state = expired if necessary
        """
        # Use DR local time
        l10n_do_date = get_l10n_do_datetime().date()
        fiscal_sequence_ids = self.search([("state", "=", "active")])

        for seq in fiscal_sequence_ids.filtered(
            lambda s: l10n_do_date >= s.expiration_date
        ):
            seq.state = "expired"

    def _get_queued_fiscal_sequence(self):
        fiscal_sequence_id = self.search(
            [
                ("state", "=", "queue"),
                ("fiscal_type_id", "=", self.fiscal_type_id.id),
                ("company_id", "=", self.company_id.id),
            ],
            order="sequence_start asc",
            limit=1,
        )
        return fiscal_sequence_id

    def get_fiscal_number(self):

        if not self.fiscal_type_id.assigned_sequence:
            return False

        if self.sequence_remaining > 0:
            sequence_next = self.sequence_id._next()

            # After consume a sequence, evaluate if sequence
            # is depleted and set state to depleted
            if (self.sequence_remaining - 1) < 1:
                self.state = "depleted"
                queue_sequence_id = self._get_queued_fiscal_sequence()
                if queue_sequence_id:
                    queue_sequence_id._action_confirm()

            return "%s%s" % (
                self.fiscal_type_id.prefix,
                str(sequence_next).zfill(self.sequence_id.padding),
            )
        else:
            raise ValidationError(
                _("No Fiscal Sequence available for this type of document.")
            )


class AccountFiscalType(models.Model):
    _name = "account.fiscal.type"
    _description = "Account Fiscal Type"
    _order = "sequence"

    name = fields.Char(
        string="Name",
        required=True, 
        copy=False,
    )
    active = fields.Boolean(
        string="Active",
        default=True
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    prefix = fields.Char(
        string="Prefix",
        copy=False,
    )
    padding = fields.Integer(
        string="Padding",
        default=8,
    )
    type = fields.Selection(
        string="Type",
        selection=[
            ("out_invoice", "Sale"),
            ("in_invoice", "Purchase"),
            ("out_refund", "Customer Credit Note"),
            ("in_refund", "Supplier Credit Note"),
            ("out_debit", "Customer Debit Note"),
            ("in_debit", "Supplier Debit Note"),
        ],
        required=True,
        default="in_invoice",
    )
    journal_type = fields.Selection(
        string="Journal Type",
        selection=[
            ("sale", "Sale"), 
            ("purchase", "Purchase")
        ], 
        compute="_compute_journal_type"
    )
    fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Fiscal Position"
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal", 
        string="Journal"
    )
    assigned_sequence = fields.Boolean(
        string="Assigned Sequence",
        help="If checked, this Fiscal Type will use a Fiscal Sequence to generate Fiscal Numbers.",
        default=True,
    )
    requires_document = fields.Boolean(
        string="Requires a document?",
        help="If checked, this Fiscal Type will require a document to be generated.",
    )

    _sql_constraints = [
        (
            "type_prefix_uniq",
            "unique (type, prefix)",
            "There must be only one Fiscal Type of this Type and Prefix",
        )
    ]

    @api.depends("type")
    def _compute_journal_type(self):
        for fiscal_type in self:
            fiscal_type.journal_type = (
                "sale" if fiscal_type.type[:3] == "out" else "purchase"
            )

    def check_format_fiscal_number(self, fiscal_number, type=''):

        if not fiscal_number:
            raise ValidationError(_('Fiscal number can not be blank'))
        
        if len(fiscal_number) < 3:
            raise ValidationError(_('This origin fiscal number must have more than 3 characters'))
        
        fiscal_type = self
        message = ''

        if not self:
            fiscal_type = self.search([
                ('prefix', '=', fiscal_number[0:3]), 
                ('type', '=', type)
            ])

        if not fiscal_type:
            if type in ('in_refund', 'out_refund'):
                message = _('The fiscal number type (%s) is not a credit note.') % fiscal_number[0:3]

            raise ValidationError(
                _('This document type (%s) does not exist.' % fiscal_number[0:3]) if not message else message
            )

        origin_out_padding = len(fiscal_number) - len(fiscal_type.prefix) if fiscal_type.prefix else len(fiscal_number)

        if origin_out_padding != fiscal_type.padding:
            raise ValidationError(
                _('The document type (%s) has (%s) digits. You are trying to input (%s) digits.') % 
                (fiscal_type.name, fiscal_type.padding, origin_out_padding)
            )
        
        if not re.match('^[0-9]+$', fiscal_number[3:]):
            raise ValidationError(
                _('After the document type, all characters must be digits from 0 to 9.')
            )

        if fiscal_type.prefix and fiscal_number[0:3] != fiscal_type.prefix:
            raise ValidationError(
                _('The document type (%s) must start with (%s)') % (fiscal_type.name, fiscal_type.prefix)
            )

        
