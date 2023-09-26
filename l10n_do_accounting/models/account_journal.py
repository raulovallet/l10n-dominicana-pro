from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

####### remove this for migration


# class NcfControlManager(models.Model):
#     _name = "ncf.control.manager"
#     _description = "NCF Control Manager"

#     journal_id = fields.Many2one(
#         comodel_name="account.journal", 
#         string="Journal"
#     )
#     l10n_latam_document_type_id = fields.Many2one(
#         comodel_name="l10n_latam.document.type", 
#         string="Document Type"
#     )
#     l10n_do_ncf_expiration_date = fields.Date(
#         string="Expiration Date"
#     )
#     l10n_do_ncf_max_number = fields.Integer(
#         string="Max Number"
#     )


    ####################


class AccountJournal(models.Model):
    _inherit = "account.journal"

    ####### remove this for migration
    # l10n_do_payment_form = fields.Selection(
    #     string="Payment Form",
    #     selection=[
    #         ("cash", "Cash"),
    #         ("bank", "Check / Transfer"),
    #         ("card", "Credit Card"),
    #         ("credit", "Credit"),
    #         ("swap", "Swap"),
    #         ("bond", "Bonds or Gift Certificate"),
    #         ("others", "Other Sale Type"),
    #     ],
    # )
    # l10n_do_ncf_control_manager_ids = fields.Many2many(
    #     "ncf.control.manager",
    #     string="NCF Control Managers"
    # )

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
