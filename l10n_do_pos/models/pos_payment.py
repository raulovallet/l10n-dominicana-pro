from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def _get_payment_values(self, payment):
        amount = sum(payment.mapped('amount'))  if len(payment) > 1 else payment.amount
        payment = payment[0] if len(payment) > 1 else payment
        payment_method = payment.payment_method_id
        payment_session = payment.session_id
        
        return {
            'amount': amount,
            'payment_type': 'inbound' if amount >= 0 else 'outbound',
            'date': payment.payment_date,
            'partner_id': payment.partner_id.id if payment.partner_id else False,
            'currency_id': payment.currency_id.id,
            'pos_session_id': payment_session.id,
            'ref': _('%s POS payments from %s') % (payment_method.name, payment_session.name),
            'pos_payment_method_id': payment_method.id,
            'journal_id': payment_method.journal_id.id,
        }

    def _create_payment_moves(self, is_reverse=False):
        
        if self and not self.mapped('session_id.config_id')[0].l10n_do_fiscal_journal:
            return super(PosPayment, self)._create_payment_moves(is_reverse)

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

        
        pos_payment_cash = self.filtered(lambda p: p.payment_method_id.is_cash_count and not p.payment_method_id.is_credit_note)
        
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
                
        for credit_note in self.filtered(lambda p: p.payment_method_id.is_credit_note and p.name):
            account_move_credit_note = self.env['account.move'].search([                    
                    ('partner_id', '=', credit_note.partner_id.id),
                    ('ref', '=', credit_note.name),
                    ('move_type', '=', 'out_refund'),
                    ('is_l10n_do_fiscal_invoice', '=', True),
                    ('company_id', '=', self.env.company.id),
                    ('state', '=', 'posted')
                ], limit=1
            )
            
            if account_move_credit_note and credit_note.amount > 0:
                account_move_credit_note.write({
                    'pos_payment_ids': credit_note.ids,
                })
                credit_note.write({
                    'account_move_id': account_move_credit_note.id
                })
                result |= account_move_credit_note

        return result

