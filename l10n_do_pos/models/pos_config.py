from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default partner',
    )
    l10n_do_fiscal_journal = fields.Boolean(
        string='Fiscal POS',
        related='invoice_journal_id.l10n_do_fiscal_journal',
    )
