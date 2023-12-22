from odoo import api, fields, models, _

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    
    is_credit_note = fields.Boolean(
        string='Credit Note',
    )

    @api.constrains('is_credit_note')
    def _check_is_credit_note(self):
        for record in self:
            if record.is_credit_note:
                if not record.split_transactions:
                    raise models.ValidationError(
                        _('Identify customer must be true if is credit note is true.'))

                if record.journal_id:
                    raise models.ValidationError(
                        _('Journal must be empty if is credit note is true.'))
