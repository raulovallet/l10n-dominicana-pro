from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    ####### remove this for migration
    l10n_do_payment_form = fields.Selection(
        string="Payment Form",
        selection=[
            ("cash", "Cash"),
            ("bank", "Check / Transfer"),
            ("card", "Credit Card"),
            ("credit", "Credit"),
            ("swap", "Swap"),
            ("bond", "Bonds or Gift Certificate"),
            ("others", "Other Sale Type"),
        ],
    )
    l10n_do_ncf_control_manager_ids = fields.Many2many(
        "res.users", string="NCF Control Managers"
    )
    journal_id = fields.Many2one(
        "account.journal", string="Journal", ondelete="cascade"
    )
    
    ####################
    l10n_do_fiscal_journal = fields.Boolean(
        string="Fiscal Journal"
    )
    payment_form = fields.Selection(
        string="Payment Form",
        selection=[
            ("cash", "Cash"),
            ("bank", "Check / Transfer"),
            ("card", "Credit Card"),
            ("credit", "Credit"),
            ("swap", "Swap"),
            ("bond", "Bonds or Gift Certificate"),
            ("others", "Other Sale Type"),
        ],
    )

    @api.constrains("l10n_do_fiscal_journal")
    def check_l10n_do_fiscal_journal(self):
        for journal in self:
            if journal.env["account.move"].search_count(
                [
                    ("journal_id", "=", journal.id),
                    ("state", "!=", "draft"),
                    ("is_l10n_do_fiscal_invoice", "=", True),
                ]
            ):
                raise ValidationError(
                    _(
                        'You can not modify the field "Fiscal Journal" if there are '
                        "validated invoices in this journal!"
                    )
                )
