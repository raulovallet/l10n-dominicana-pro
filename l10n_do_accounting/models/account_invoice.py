# TODO: poner authorship en todos los archivos .py (xml tamb?)

import logging
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf as ncf_validation
except (ImportError, IOError) as err:
    _logger.debug(err)

ncf_dict = {
    "B01": "fiscal",
    "B02": "consumo",
    "B15": "gov",
    "B14": "especial",
    "B12": "unico",
    "B16": "export",
    "B03": "debit",
    "B04": "credit",
    "B13": "minor",
    "B11": "informal",
    "B17": "exterior",
}


class AccountInvoice(models.Model):
    _inherit = "account.move"

    fiscal_type_id = fields.Many2one(
        string='Fiscal type',
        comodel_name="account.fiscal.type",
        index=True,
    )
    available_fiscal_type_ids = fields.Many2many(
        string="Available Fiscal Type",
        comodel_name="account.fiscal.type",
        compute='_compute_available_fiscal_type'
    )
    fiscal_sequence_id = fields.Many2one(
        comodel_name="account.fiscal.sequence",
        string="Fiscal Sequence",
        copy=False,
        compute="_compute_fiscal_sequence",
        store=True,
    )
    income_type = fields.Selection(
        string="Income Type",
        selection=[
            ("01", "01 - Operating Revenues (Non-Financial)"),
            ("02", "02 - Financial Revenues"),
            ("03", "03 - Extraordinary Revenues"),
            ("04", "04 - Rental Revenues"),
            ("05", "05 - Revenues from Sale of Depreciable Assets"),
            ("06", "06 - Other Revenues"),
        ],
        copy=False,
        default=lambda self: self._context.get("income_type", "01"),
    )
    expense_type = fields.Selection(
        copy=False,
        selection=[
            ("01", "01 - Personnel Expenses"),
            ("02", "02 - Expenses for Labor, Supplies, and Services"),
            ("03", "03 - Leases"),
            ("04", "04 - Fixed Asset Expenses"),
            ("05", "05 - Representation Expenses"),
            ("06", "06 - Other Allowable Deductions"),
            ("07", "07 - Financial Expenses"),
            ("08", "08 - Extraordinary Expenses"),
            ("09", "09 - Purchases and Expenses that form part of the Cost of Sales"),
            ("10", "10 - Acquisitions of Assets"),
            ("11", "11 - Insurance Expenses"),
        ],
        string="Cost & Expense Type",
    )
    annulation_type = fields.Selection(
        string="Annulment Type",
        selection=[
            ("01", "01 - Deterioration of Pre-printed Invoice"),
            ("02", "02 - Printing Errors (Pre-printed Invoice)"),
            ("03", "03 - Defective Printing"),
            ("04", "04 - Correction of Information"),
            ("05", "05 - Change of Products"),
            ("06", "06 - Product Returns"),
            ("07", "07 - Omission of Products"),
            ("08", "08 - Errors in Sequence of NCF"),
            ("09", "09 - Due to Cessation of Operations"),
            ("10", "10 - Loss or Theft of Invoice Books"),
        ],
        copy=False,
    )
    origin_out = fields.Char(
        string="Affects",
        copy=False,
    )
    ncf_expiration_date = fields.Date(
        string="Valid until",
        store=True,
        copy=False,
        required=False
    )
    is_l10n_do_fiscal_invoice = fields.Boolean(
        string="Is Fiscal Invoice",
        compute="_compute_is_l10n_do_fiscal_invoice",
        store=True,
    )
    assigned_sequence = fields.Boolean(
        related="fiscal_type_id.assigned_sequence",
    )
    fiscal_sequence_status = fields.Selection(
        selection=[
            ("no_fiscal", "No fiscal"),
            ("fiscal_ok", "Ok"),
            ("almost_no_sequence", "Almost no sequence"),
            ("no_sequence", "Depleted"),
        ],
        compute="_compute_fiscal_sequence_status",
    )
    is_debit_note = fields.Boolean(
        string="Is debit note"
    )

    @api.depends("is_l10n_do_fiscal_invoice", "move_type", "journal_id", "partner_id")
    def _compute_available_fiscal_type(self):
        self.available_fiscal_type_ids = False
        for inv in self.filtered(lambda x: x.journal_id and x.is_l10n_do_fiscal_invoice and x.partner_id):
            inv.available_fiscal_type_ids = self.env['account.fiscal.type'].search(inv._get_fiscal_domain())

    def _get_fiscal_domain(self):
        return [('type', '=', self.move_type)]

    @api.depends("state", "journal_id")
    def _compute_is_l10n_do_fiscal_invoice(self):
        for inv in self:
            inv.is_l10n_do_fiscal_invoice = inv.journal_id.l10n_do_fiscal_journal

    @api.depends(
        "journal_id",
        "is_l10n_do_fiscal_invoice",
        "state",
        "fiscal_type_id",
        "invoice_date",
        "move_type",
        "is_debit_note",
    )

    def _compute_fiscal_sequence(self):
        """ Compute the sequence and fiscal position to be used depending on
            the fiscal type that has been set on the invoice (or partner).
        """
        for inv in self.filtered(lambda i: i.state == "draft"):
            if inv.is_debit_note:
                
                debit_map = {"in_invoice": "in_debit", "out_invoice": "out_debit"}
                fiscal_type = self.env["account.fiscal.type"].search(
                    [("type", "=", debit_map[inv.move_type])], limit=1
                )
                inv.fiscal_type_id = fiscal_type.id

            else:
                fiscal_type = inv.fiscal_type_id

            if (
                inv.is_l10n_do_fiscal_invoice
                and fiscal_type
                and fiscal_type.assigned_sequence
            ):

                inv.assigned_sequence = fiscal_type.assigned_sequence
                inv.fiscal_position_id = fiscal_type.fiscal_position_id

                domain = [
                    ("company_id", "=", inv.company_id.id),
                    ("fiscal_type_id", "=", fiscal_type.id),
                    ("state", "=", "active"),
                ]
                if inv.invoice_date:
                    domain.append(("expiration_date", ">=", inv.invoice_date))
                else:
                    today = fields.Date.context_today(inv)
                    domain.append(("expiration_date", ">=", today))

                fiscal_sequence_id = inv.env["account.fiscal.sequence"].search(
                    domain, order="expiration_date, id desc", limit=1,
                )

                if not fiscal_sequence_id:
                    pass
                elif fiscal_sequence_id.state == "active":
                    inv.fiscal_sequence_id = fiscal_sequence_id
                else:
                    inv.fiscal_sequence_id = False
            else:
                inv.fiscal_sequence_id = False

    @api.depends(
        "fiscal_sequence_id",
        "fiscal_sequence_id.sequence_remaining",
        "fiscal_sequence_id.remaining_percentage",
        "state",
        "journal_id",
    )
    def _compute_fiscal_sequence_status(self):
        """ Identify the percentage fiscal sequences that has been used so far.
            With this result the user can be warned if it's above the threshold
            or if there's no more sequences available.
        """
        for inv in self:

            if not inv.is_l10n_do_fiscal_invoice or not inv.fiscal_sequence_id:
                inv.fiscal_sequence_status = "no_fiscal"
            else:
                fs_id = inv.fiscal_sequence_id  # Fiscal Sequence
                remaining = fs_id.sequence_remaining
                warning_percentage = fs_id.remaining_percentage
                seq_length = fs_id.sequence_end - fs_id.sequence_start + 1

                remaining_percentage = round((remaining / seq_length), 2) * 100

                if remaining_percentage > warning_percentage:
                    inv.fiscal_sequence_status = "fiscal_ok"
                elif remaining > 0 and remaining_percentage <= warning_percentage:
                    inv.fiscal_sequence_status = "almost_no_sequence"
                else:
                    inv.fiscal_sequence_status = "no_sequence"
    
    # TODO: Migrate this
    # @api.constrains("state", "tax_line_ids")
    # def validate_special_exempt(self):
    #     """ Validates an invoice with Regímenes Especiales fiscal type
    #         does not contain nor ITBIS or ISC.
    #         See DGII Norma 05-19, Art 3 for further information.
    #     """
    #     for inv in self.filtered(lambda i: i.is_l10n_do_fiscal_invoice):
    #         if (
    #             inv.move_type == "out_invoice"
    #             and inv.state in ("open", "cancel")
    #             and ncf_dict.get(inv.fiscal_type_id.prefix) == "especial"
    #         ):
    #             # If any invoice tax in ITBIS or ISC
    #             taxes = ("ITBIS", "ISC")
    #             if any(
    #                 [
    #                     tax
    #                     for tax in inv.tax_line_ids.mapped("tax_id").filtered(
    #                         lambda tax: tax.tax_group_id.name in taxes
    #                         and tax.amount != 0
    #                     )
    #                 ]
    #             ):
    #                 raise UserError(
    #                     _(
    #                         "You cannot validate and invoice of Fiscal Type "
    #                         "Regímen Especial with ITBIS/ISC.\n\n"
    #                         "See DGII General Norm 05-19, Art. 3 for further "
    #                         "information"
    #                     )
    #                 )

    @api.constrains("state", "invoice_line_ids", "partner_id")
    def validate_products_export_ncf(self):
        """ Validates that an invoices with a partner from country != DO
            and products type != service must have Exportaciones NCF.
            See DGII Norma 05-19, Art 10 for further information.
        """
        for inv in self:
            if (
                inv.move_type == "out_invoice"
                and inv.state in ("posted", "cancel")
                and inv.partner_id.country_id
                and inv.partner_id.country_id.code != "DO"
                and inv.is_l10n_do_fiscal_invoice
            ):
                if any(
                    [
                        p
                        for p in inv.invoice_line_ids.mapped("product_id")
                        if p.type != "service"
                    ]
                ):
                    if ncf_dict.get(inv.fiscal_type_id.prefix) == "exterior":
                        raise UserError(
                            _(
                                "Goods sales to overseas customers must have "
                                "Exportaciones Fiscal Type"
                            )
                        )
                elif ncf_dict.get(inv.fiscal_type_id.prefix) == "consumo":
                    raise UserError(
                        _(
                            "Service sales to oversas customer must have "
                            "Consumo Fiscal Type"
                        )
                    )
    # TODO: MIGRATE THIS
    # @api.constrains("state", "tax_line_ids")
    # def validate_informal_withholding(self):
    #     """ Validates an invoice with Comprobante de Compras has 100% ITBIS
    #         withholding.
    #         See DGII Norma 05-19, Art 7 for further information.
    #     """
    #     for inv in self.filtered(
    #         lambda i: i.move_type == "in_invoice" and i.state == "open"
    #     ):
    #         if (
    #             ncf_dict.get(inv.fiscal_type_id.prefix) == "informal"
    #             and inv.is_l10n_do_fiscal_invoice
    #         ):

    #             # If the sum of all taxes of category ITBIS is not 0
    #             if sum(
    #                 [
    #                     tax.amount
    #                     for tax in inv.tax_line_ids.mapped("tax_id").filtered(
    #                         lambda t: t.tax_group_id.name == "ITBIS"
    #                     )
    #                 ]
    #             ):
    #                 raise UserError(_("You must withhold 100% of ITBIS"))

    @api.onchange("journal_id", "partner_id")
    def _onchange_journal_id(self):
        """ Set the Fiscal Type and the Fiscal Sequence to False, if the
            invoice is not a fiscal invoice for l10n_do.
        """
        if not self.is_l10n_do_fiscal_invoice:
            self.fiscal_type_id = False
            self.fiscal_sequence_id = False

        return super(AccountInvoice, self)._onchange_journal_id()

    @api.onchange("fiscal_type_id")
    def _onchange_fiscal_type(self):
        """ Set the Journal to a fiscal journal if a Fiscal Type is set to the
            invoice, making it a a fiscal invoice for l10n_do.
        """
        if self.is_l10n_do_fiscal_invoice and self.fiscal_type_id:
            if ncf_dict.get(self.fiscal_type_id.prefix) == "minor":
                self.partner_id = self.company_id.partner_id

            fiscal_type = self.fiscal_type_id
            fiscal_type_journal = fiscal_type.journal_id
            if fiscal_type_journal and fiscal_type_journal != self.journal_id:
                self.journal_id = fiscal_type_journal

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """ Set the Journal to a fiscal journal if a Fiscal Type is set to the
            invoice, making it a a fiscal invoice for l10n_do.
        """
        if self.is_l10n_do_fiscal_invoice:
            
            fiscal_type_object = self.env["account.fiscal.type"]
            if self.partner_id and self.move_type == "out_invoice" and not self.fiscal_type_id:
                
                self.fiscal_type_id = self.partner_id.sale_fiscal_type_id

            elif self.partner_id and self.move_type == "in_invoice":
                
                self.expense_type = self.partner_id.expense_type

                if self.partner_id.id == self.company_id.partner_id.id:
                    fiscal_type = fiscal_type_object.search(
                        [("type", "=", self.move_type), ("prefix", "=", "B13")], limit=1
                    )
                    if not fiscal_type:
                        raise ValidationError(
                            _(
                                "A fiscal type for Minor Expenses does not exist"
                                " and you have to create one."
                            )
                        )
                    self.fiscal_type_id = fiscal_type
                    return super(AccountInvoice, self)._onchange_partner_id()
                self.fiscal_type_id = self.partner_id.purchase_fiscal_type_id

            elif self.partner_id and not self.fiscal_type_id and self.move_type in ['in_refund', 'out_refund']:

                fiscal_refund = fiscal_type_object.search([
                    ('type', '=', self.move_type)
                ])
                self.fiscal_type_id = fiscal_refund[0] if fiscal_refund else False

        return super(AccountInvoice, self)._onchange_partner_id()

    def _post(self, soft=True):
        """ Before an invoice is changed to the 'open' state, validate that all
            informations are valid regarding Norma 05-19 and if there are
            available sequences to be used just before validation
        """
        for inv in self:

            if inv.is_l10n_do_fiscal_invoice and inv.is_invoice():
                if inv.amount_total == 0:
                    raise UserError(
                        _(
                            u"You cannot validate an invoice whose "
                            u"total amount is equal to 0"
                        )
                    )

                if inv.fiscal_type_id and not inv.fiscal_type_id.assigned_sequence:
                    inv.fiscal_type_id.check_format_fiscal_number(inv.ref)

                # Because a Fiscal Sequence can be depleted while an invoice
                # is waiting to be validated, compute fiscal_sequence_id again
                # on invoice validate.
                inv._compute_fiscal_sequence()

                if not inv.ref \
                        and not inv.fiscal_sequence_id \
                        and inv.fiscal_type_id.assigned_sequence:
                    raise ValidationError(_("There is not active Fiscal Sequence for this type of document."))

                if inv.move_type == "out_invoice":
                    if not inv.partner_id.sale_fiscal_type_id:
                        inv.partner_id.sale_fiscal_type_id = inv.fiscal_type_id

                if inv.move_type == "in_invoice":

                    if not inv.partner_id.purchase_fiscal_type_id:
                        inv.partner_id.purchase_fiscal_type_id = inv.fiscal_type_id
                    if not inv.partner_id.expense_type:
                        inv.partner_id.expense_type = inv.expense_type

                if inv.fiscal_type_id.requires_document and not inv.partner_id.vat:
                    raise UserError(
                        _(
                            "Partner [{}] {} doesn't have RNC/Céd, "
                            "is required for NCF type {}"
                        ).format(
                            inv.partner_id.id,
                            inv.partner_id.name,
                            inv.fiscal_type_id.name,
                        )
                    )

                elif inv.move_type in ("out_invoice", "out_refund"):
                    if (
                            inv.amount_untaxed_signed >= 250000
                            and inv.fiscal_type_id.prefix != "B12"
                            and not inv.partner_id.vat
                    ):
                        raise UserError(
                            _(
                                u"if the invoice amount is greater than "
                                u"RD$250,000.00 "
                                u"the customer should have RNC or Céd"
                                u"for make invoice"
                            )
                        )

                # Check refund stuff
                if inv.origin_out and inv.move_type in ('out_refund', 'in_refund'):
                    self.env['account.fiscal.type'].check_format_fiscal_number(
                        inv.origin_out,
                        'in_invoice' if inv.move_type == 'in_refund' else 'out_invoice'
                    )

                    origin_invoice = self.env['account.move'].search([
                        ('ref', '=', inv.origin_out),
                        ('partner_id', '=', inv.partner_id.id),
                        ('state', '=', 'posted'),
                        ('is_l10n_do_fiscal_invoice', '=', True),
                        ('move_type', '=', 'in_invoice' if inv.move_type == 'in_refund' else 'out_invoice')
                    ], limit=1)

                    if not origin_invoice:
                        raise UserError(_(
                            'The invoice ({}) to which the credit note refers does not exist in the system or is not under the name of {}'
                        ).format(inv.origin_out, inv.partner_id.name)
                                        )

                    delta_time = inv.invoice_date - origin_invoice.invoice_date

                    if delta_time.days > 30 and inv.line_ids.filtered(
                            lambda l: l.tax_line_id and 'itbis' in l.tax_line_id.name.lower()):
                        raise UserError(_(
                            'The invoice ({}) to which this credit note refers is more than 30 days old ({}), therefore the ITBIS tax must be removed.'
                        ).format(inv.origin_out, delta_time.days)
                                        )

        res = super(AccountInvoice, self)._post(soft)

        for inv in self:
            if inv.is_l10n_do_fiscal_invoice \
                    and not inv.ref \
                    and inv.fiscal_type_id.assigned_sequence \
                    and inv.is_invoice() \
                    and inv.state == "posted":
                inv.write({
                    'ref': inv.fiscal_sequence_id.get_fiscal_number(),
                    'ncf_expiration_date': inv.fiscal_sequence_id.expiration_date
                })

        return res

    #esta funcion no esta en la 16.0.2.0.9
    # def validate_fiscal_purchase(self):
    #     for inv in self.filtered(
    #         lambda i: i.move_type == "in_invoice" and i.state == "draft"
    #     ):
    #         ncf = inv.ref if inv.ref else None
    #         if ncf and ncf_dict.get(inv.fiscal_type_id.prefix) == "fiscal":
    #             if ncf[-10:-8] == "02" or ncf[1:3] == "32":
    #                 raise ValidationError(
    #                     _(
    #                         "NCF *{}* does not correspond with the fiscal type\n\n"
    #                         "You cannot register Consumo (02 or 32) for purchases"
    #                     ).format(ncf)
    #                 )
    #
    #             elif inv.fiscal_type_id.requires_document and not inv.partner_id.vat:
    #                 raise ValidationError(
    #                     _(
    #                         "Partner [{}] {} doesn't have RNC/Céd, "
    #                         "is required for NCF type {}"
    #                     ).format(
    #                         inv.partner_id.id,
    #                         inv.partner_id.name,
    #                         inv.fiscal_type_id.name,
    #                     )
    #                 )
    #
    #             elif not ncf_validation.is_valid(ncf):
    #                 raise UserError(
    #                     _(
    #                         "NCF wrongly typed\n\n"
    #                         "This NCF *{}* does not have the proper structure, "
    #                         "please validate if you have typed it correctly."
    #                     ).format(ncf)
    #                 )
    #
    #             ncf_in_invoice = (
    #                 inv.search_count(
    #                     [
    #                         ("id", "!=", inv.id),
    #                         ("company_id", "=", inv.company_id.id),
    #                         ("partner_id", "=", inv.partner_id.id),
    #                         ("ref", "=", ncf),
    #                         ("state", "in", ("draft", "open", "paid", "cancel")),
    #                         ("move_type", "in", ("in_invoice", "in_refund")),
    #                     ]
    #                 )
    #                 if inv.id
    #                 else inv.search_count(
    #                     [
    #                         ("partner_id", "=", inv.partner_id.id),
    #                         ("company_id", "=", inv.company_id.id),
    #                         ("ref", "=", ncf),
    #                         ("state", "in", ("draft", "open", "paid", "cancel")),
    #                         ("move_type", "in", ("in_invoice", "in_refund")),
    #                     ]
    #                 )
    #             )
    #
    #             if ncf_in_invoice:
    #                 raise ValidationError(
    #                     _(
    #                         "NCF already used in another invoice\n\n"
    #                         "The NCF *{}* has already been registered in another "
    #                         "invoice with the same supplier. Look for it in "
    #                         "invoices with canceled or draft states"
    #                     ).format(ncf)
    #                 )

    def action_invoice_cancel(self):

        # if self.journal_id.l10n_do_fiscal_journal:
        fiscal_invoice = self.filtered(
            lambda inv: inv.journal_id.l10n_do_fiscal_journal)
        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time."))

        if fiscal_invoice:
            action = self.env.ref(
                'l10n_do_accounting.action_account_invoice_cancel'
            ).read()[0]
            action['context'] = {'default_invoice_id': fiscal_invoice.id}
            return action
                

    def button_cancel(self, force_cancel=False):

        if self.journal_id.l10n_do_fiscal_journal and force_cancel == False:

            return self.action_invoice_cancel()
        else:
            return super(AccountInvoice, self).button_cancel()

        
        

    @api.returns("self")
    def refund(self, invoice_date=None, date=None, description=None, journal_id=None):

        context = dict(self._context or {})
        refund_type = context.get("refund_type")
        amount = context.get("amount")
        account = context.get("account")

        if not refund_type:
            return super(AccountInvoice, self).refund(
                invoice_date=invoice_date,
                date=date,
                description=description,
                journal_id=journal_id,
            )

        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self.with_context(
                refund_type=refund_type, amount=amount, account=account
            )._prepare_refund(
                invoice,
                invoice_date=invoice_date,
                date=date,
                description=description,
                journal_id=journal_id,
            )
            refund_invoice = self.create(values)
            if invoice.move_type == "out_invoice":
                message = _(
                    "This customer invoice credit note has been created from: "
                    "<a href=# data-oe-model=account.move data-oe-id=%d>%s"
                    "</a><br>Reason: %s"
                ) % (invoice.id, invoice.number, description)
            else:
                message = _(
                    "This vendor bill credit note has been created from: <a "
                    "href=# data-oe-model=account.move data-oe-id=%d>%s</a>"
                    "<br>Reason: %s"
                ) % (invoice.id, invoice.number, description)

            refund_invoice.message_post(body=message)
            refund_invoice._compute_fiscal_sequence()
            new_invoices += refund_invoice
        return new_invoices

    def _get_l10n_do_amounts(self, company_currency=False):
        """
        Method used to to prepare dominican fiscal invoices amounts data. Widely used
        on reports and electronic invoicing.

        Returned values:

        itbis_amount: Total ITBIS
        itbis_taxable_amount: Monto Gravado Total (con ITBIS)
        itbis_exempt_amount: Monto Exento
        """
        self.ensure_one()
        amount_field = company_currency and "balance" or "price_subtotal"
        sign = -1 if (company_currency and self.is_inbound()) else 1

        itbis_tax_group = self.env.ref("l10n_do.group_itbis", False)

        taxed_move_lines = self.line_ids.filtered("tax_line_id")
        itbis_taxed_move_lines = taxed_move_lines.filtered(
            lambda l: itbis_tax_group in l.tax_line_id.mapped("tax_group_id")
            and l.tax_line_id.amount > 0
        )

        itbis_taxed_product_lines = self.invoice_line_ids.filtered(
            lambda l: itbis_tax_group in l.tax_ids.mapped("tax_group_id")
        )

        return {
            "itbis_amount": sign * sum(itbis_taxed_move_lines.mapped(amount_field)),
            "itbis_taxable_amount": sign
            * sum(
                line[amount_field]
                for line in itbis_taxed_product_lines
                if line.price_total != line.price_subtotal
            ),
            "itbis_exempt_amount": sign
            * sum(
                line[amount_field]
                for line in itbis_taxed_product_lines
                if any(True for tax in line.tax_ids if tax.amount == 0)
            ),
        }

    @api.model_create_multi
    def create(self, vals_list):
        # Add default fiscal type from sales and purchase orders

        res = super(AccountInvoice, self).create(vals_list)

        fiscal_invoices = res.filtered(
            lambda i: i.is_l10n_do_fiscal_invoice and not i.fiscal_type_id and i.is_invoice()
        )
        for fiscal_invoice in fiscal_invoices:
            fiscal_invoice._onchange_partner_id()
            fiscal_invoice.write({
                'ref': '',
                'payment_reference': fiscal_invoice.ref
            })

        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_fiscal_invoice(self):
        for invoice in self:
            if invoice.is_l10n_do_fiscal_invoice and invoice.is_invoice() and invoice.ref:
                raise UserError(_("You cannot delete a fiscal invoice that has been validated."))
        

    # def invoice_print(self):
    #     # Companies which has installed l10n_do localization use
    #     # l10n_do fiscal invoice template
    #     l10n_do_coa = self.env.ref("l10n_do.do_chart_template")
    #     if self.journal_id.company_id.chart_template_id.id == l10n_do_coa.id:
    #         report_id = self.env.ref("l10n_do_accounting.l10n_do_account_invoice")
    #         return report_id.report_action(self)

    #     return super(AccountInvoice, self).invoice_print()
