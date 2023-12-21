from odoo import api, fields, models, _
from odoo.tools import float_is_zero

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def _get_payment_values(self, payment):
        amount = sum(payment.mapped('amount'))  if len(payment) > 1 else payment.amount
        payment = payment[0] if len(payment) > 1 else payment

        return {
            'journal_id': payment.payment_method_id.journal_id.id,
            'partner_id': payment.partner_id.id if payment.partner_id else False,
            'amount': amount,
            'payment_type': 'inbound' if amount >= 0 else 'outbound',
            'date': payment.payment_date,
            'currency_id': payment.currency_id.id,
        }

    def _create_payment_moves(self):
        
        if self and not self.mapped('session_id.config_id')[0].l10n_do_fiscal_journal:
            return super(PosPayment, self)._create_payment_moves()

        result = self.env['account.move']
        for payment in self.filtered(lambda p: not p.payment_method_id.is_cash_count and not p.payment_method_id.is_credit_note):
            order = payment.pos_order_id
            payment_method = payment.payment_method_id
            
            if payment_method.type == 'pay_later' or float_is_zero(payment.amount, precision_rounding=order.currency_id.rounding):
                continue

            account_payment = self.env['account.payment'].create(
                self._get_payment_values(payment)
            )
            account_payment.action_post()
            account_payment.move_id.write({
                'pos_payment_ids': payment.ids,
            })
            payment.write({
                'account_move_id': account_payment.move_id.id
            })
            result |= account_payment.move_id

        pos_payment_cash = self.filtered(lambda p: p.payment_method_id.is_cash_count and not not p.payment_method_id.is_credit_note)
        if pos_payment_cash:
            account_payment_cash = self.env['account.payment'].create(
                self._get_payment_values(pos_payment_cash)
            )
            account_payment_cash.action_post()
            account_payment_cash.move_id.write({
                'pos_payment_ids': pos_payment_cash.ids,
            })
            pos_payment_cash.write({
                'account_move_id': account_payment_cash.move_id.id
            })
            result |= account_payment_cash.move_id
        
        # credit_notes = self.filtered(lambda p: p.payment_method_id.is_credit_note)
        # if credit_notes:
        #     account_payment_credit_note = self.env['account.payment'].create(
        #         self._get_payment_values(credit_notes)
        #     )
        #     account_payment_credit_note.action_post()
        #     account_payment_credit_note.move_id.write({
        #         'pos_payment_ids': credit_notes.ids,
        #     })
        #     credit_notes.write({
        #         'account_move_id': account_payment_credit_note.move_id.id
        #     })
        #     result |= account_payment_credit_note.move_id

        return result

