from odoo import api, fields, models, _
from odoo.tools import float_is_zero

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def _create_payment_moves(self):
        if self and not self.mapped('session_id').mapped('config_id')[0].l10n_do_fiscal_journal:
            return super(PosPayment, self)._create_payment_moves()

        result = self.env['account.move']
        for payment in self.filtered(lambda p: not p.payment_method_id.is_cash_count):
            order = payment.pos_order_id
            payment_method = payment.payment_method_id
            if payment_method.type == 'pay_later' or float_is_zero(payment.amount, precision_rounding=order.currency_id.rounding):
                continue
            
            payment = self.env['account.payment'].create({
                'journal_id': payment_method.journal_id.id,
                'partner_id': payment.partner_id.id,
                'amount': payment.amount,
                'payment_type': 'inbound',
                'date': payment.payment_date,
            })
            payment.action_post()
            payment.move_id.write({
                'pos_payment_ids': payment.ids,
            })

            result |= payment.move_id

        pos_payment_cash = self.filtered(lambda p: p.payment_method_id.is_cash_count)
        if pos_payment_cash:
            payment_cash = self.env['account.payment'].create({
                'journal_id': pos_payment_cash[0].payment_method_id.journal_id.id,
                'partner_id': pos_payment_cash[0].partner_id.id,
                'amount': sum(pos_payment_cash.mapped('amount')),
                'payment_type': 'inbound',
                'date': pos_payment_cash[0].payment_date,
            })
            payment_cash.action_post()
            for move_line in payment_cash.move_id.line_ids:
                pass
            payment_cash.move_id.write({
                'pos_payment_ids': pos_payment_cash.ids,
            })
            result |= payment_cash.move_id

        return result
