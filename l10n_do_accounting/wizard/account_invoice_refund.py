import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf as ncf_validation
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        context = dict(self._context or {})
        invoice_ids = self.env["account.move"].browse(context.get("active_ids"))
        test = set(invoice_ids.mapped("is_l10n_do_fiscal_invoice"))
        test = set(invoice_ids.mapped("move_type"))
        res.update({
            'is_fiscal_refund': set(invoice_ids.mapped("is_l10n_do_fiscal_invoice")) == {True},
            'is_vendor_refund': set(invoice_ids.mapped("move_type")) == {'in_invoice'}
        })

        return res

    @api.model
    def _get_refund_method_selection(self):
        if self._context.get("debit_note", False):
            return [
                ('refund', 'Partial Debit note'),
                ('cancel', 'Full Debit note'),
            ]
        return [
            ('refund', 'Partial Refund'),
            ('cancel', 'Full Refund'),
            ('modify', 'Full refund and new draft invoice')
        ]

    refund_method = fields.Selection(
        selection=_get_refund_method_selection,
        default="refund",
        string='Credit Method', 
        required=True,
        help='Choose how you want to credit this invoice. You cannot "modify" nor "cancel" if the invoice is already reconciled.'
    )
    is_vendor_refund = fields.Boolean(
        string='Vendor refund',
    )
    refund_ref = fields.Char(
        string='NCF'
    )
    ncf_expiration_date = fields.Date(
        string="Valid until",
    )
    is_fiscal_refund = fields.Boolean(
        string='Fiscal refund'
    )
    
    def compute_refund(self, mode="refund"):
        xml_id = False
        created_inv = []
        for wizard in self:

            inv_obj = self.env["account.move"]
            context = dict(self._context or {})
            for inv in inv_obj.browse(context.get("active_ids")):
                if inv.state in ["draft", "cancel"]:
                    raise UserError(
                        _(
                            "Cannot create credit note for the draft/cancelled "
                            "invoice."
                        )
                    )
                if inv.reconciled and mode in ("cancel", "modify"):
                    raise UserError(
                        _(
                            "Cannot create a credit note for the invoice which is "
                            "already reconciled, invoice should be unreconciled "
                            "first, then only you can add credit note for "
                            "this invoice."
                        )
                    )

                date = wizard.date or False
                description = wizard.description or inv.name
                refund_ref = wizard.refund_ref
                action_map = {
                    "out_invoice": "action_invoice_out_refund",
                    "out_refund": "action_invoice_tree1",
                    "in_invoice": "action_invoice_in_refund",
                    "in_refund": "action_invoice_tree2",
                }
                xml_id = action_map[inv.move_type]
        if xml_id:
            result = self.env.ref("account.%s" % xml_id).read()[0]
            invoice_domain = safe_eval(result["domain"])
            invoice_domain.append(("id", "in", created_inv))
            result["domain"] = invoice_domain
            return result
        return True

    # TODO: Save for debit note
    # def invoice_debit_note(self):
    #     xml_id = False
    #     created_inv = []
    #     for wizard in self:
    #         inv_obj = self.env["account.move"]
    #         context = dict(self._context or {})
    #         for inv in inv_obj.browse(context.get("active_ids")):
    #             if inv.state in ["draft", "cancel"]:
    #                 raise UserError(
    #                     _(
    #                         "Cannot create debit note for the draft/cancelled "
    #                         "invoice."
    #                     )
    #                 )

    #             debit_map = {"out_debit": "out_invoice", "in_debit": "in_invoice"}

    #             date = wizard.date or wizard.invoice_date
    #             description = wizard.description or inv.name
    #             vendor_ref = wizard.refund_ref
    #             fiscal_type = self.env["account.fiscal.type"].search(
    #                 [("type", "=", context.get("debit_note"))], limit=1
    #             )

    #             values = {
    #                 "partner_id": inv.partner_id.id,
    #                 "ref": vendor_ref,
    #                 "invoice_date": date,
    #                 "income_type": inv.income_type,
    #                 "expense_type": inv.expense_type,
    #                 "is_debit_note": True,
    #                 "origin_out": inv.ref,
    #                 "type": debit_map[context.get("debit_note")],
    #                 "fiscal_type_id": fiscal_type.id,
    #                 "invoice_line_ids": [
    #                     (
    #                         0,
    #                         0,
    #                         {
    #                             "name": description,
    #                             "account_id": wizard.account_id.id,
    #                             "price_unit": amount,
    #                         },
    #                     )
    #                 ],
    #                 "journal_id": inv.journal_id.id,
    #             }
    #             debit_note = inv_obj.create(values)
    #             created_inv.append(debit_note.id)
    #             invoice_type = {
    #                 "out_invoice": _("customer debit note"),
    #                 "in_invoice": _("vendor debit note"),
    #             }
    #             message = _(
    #                 "This %s has been created from: <a href=# data-oe-"
    #                 "model=account.move data-oe-id=%d>%s</a>"
    #             ) % (invoice_type[inv.move_type], inv.id, inv.number)
    #             debit_note.message_post(body=message)
    #             if wizard.refund_method == "apply_refund":
    #                 debit_note.action_invoice_open()

    #             action_map = {
    #                 "out_invoice": "action_invoice_out_debit_note",
    #                 "in_invoice": "action_vendor_in_debit_note",
    #             }
    #             xml_id = action_map[inv.move_type]
    #     if xml_id:
    #         result = self.env.ref("l10n_do_accounting.%s" % xml_id).read()[0]
    #         invoice_domain = safe_eval(result["domain"])
    #         invoice_domain.append(("id", "in", created_inv))
    #         result["domain"] = invoice_domain
    #         return result
    #     return True
    
    def reverse_moves(self, is_modify):
        self.ensure_one()

        if self.refund_ref and self.is_fiscal_refund:
            
            self.env['account.fiscal.type'].check_format_fiscal_number(
                self.refund_ref,
                'in_refund'
            )

        return super(AccountMoveReversal, self).reverse_moves(is_modify)
    
    def _prepare_default_reversal(self, move):
        
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        
        if self.is_fiscal_refund:
            res.update({
                'ref': self.refund_ref,
                'origin_out': move.ref,
                'expense_type': move.expense_type,
                'income_type': move.income_type,
                'ncf_expiration_date': self.ncf_expiration_date,
                'fiscal_type_id': False
            })
        
        return res