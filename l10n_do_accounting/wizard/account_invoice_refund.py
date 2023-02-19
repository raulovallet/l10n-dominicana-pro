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

        res["is_fiscal_refund"] = set(
            invoice_ids.mapped("is_l10n_do_fiscal_invoice")
        ) == {True}

        return res

    @api.model
    def _get_default_is_vendor_refund(self):
        return self._context.get("move_type", False) == "in_invoice"

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
    
    is_vendor_refund = fields.Boolean(default=_get_default_is_vendor_refund,)
    refund_ref = fields.Char()
    is_fiscal_refund = fields.Boolean()

    
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

    
    def invoice_refund(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            invoice = self.env["account.move"].browse(active_id)
            # TODO
            if self.refund_ref and self.is_fiscal_refund:
                ncf = self.refund_ref[0:3]
                ncf_digits = len(self.refund_ref)
                # TODO: Hacer las validaciones con el tipo de comprobante y no directo
                #  en e codigo.
                if (
                    self._context.get("debit_note")
                    and ncf not in ("B03", "E33")
                ):
                    raise UserError(
                        _(
                            "Debit Notes must be type B03 or E33, this NCF "
                            "structure does not comply."
                        )
                    )
                elif ncf not in ("B04", "E34"):
                    raise UserError(
                        _(
                            ("Credit Notes must be type B04 or E34, this NCF (Type %s)"
                             " structure does not comply.") % ncf
                        )
                    )
                elif (ncf_digits != 11 and ncf == 'B04') \
                        or (ncf_digits != 13 and ncf == 'E34'):
                    raise UserError(
                        _(
                            ("The number of fiscal sequence in this voucher is "
                             "incorrect, please double check the fiscal sequence")
                        )
                    )

        return super(AccountMoveReversal, self).invoice_refund()
    
    def _prepare_default_reversal(self, move):
        
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        
        if self.is_fiscal_refund:
            res.update({
                'ref': False,
                'origin_out': move.ref,
                'expense_type': move.expense_type,
                'income_type': move.income_type
            })
        
        return res
