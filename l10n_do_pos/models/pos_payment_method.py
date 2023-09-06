from odoo import api, fields, models, _

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    
    is_credit_note = fields.Boolean(
        string='Credit Note',
    )

    # TODO: check if split_transactions is true and journal_id is should be a false