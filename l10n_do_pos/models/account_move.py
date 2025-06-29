from odoo import models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def check_pos_session(self):
        for move in self:
            # Check if the move is an invoice and linked to a POS session
            if move.move_type in ('out_invoice', 'out_refund'):
                pos_orders = self.env['pos.order'].search([('account_move', '=', move.id)])
                if pos_orders:
                    # Filter sessions that are open
                    open_sessions = pos_orders.mapped('session_id').filtered(lambda s: s.state == 'opened')
                    if open_sessions:
                        session_names = ', '.join(open_sessions.mapped('name'))
                        raise UserError(_(
                            "This invoice is linked to an open POS session (%s), you cannot modify it, "
                            "please make a credit note or close the session." % session_names
                        ))

    def button_cancel(self):
        self.check_pos_session()
        return super(AccountMove, self).button_cancel()
    
    def button_draft(self):
        self.check_pos_session()
        return super(AccountMove, self).button_draft()