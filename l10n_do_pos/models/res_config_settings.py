from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_do_fiscal_journal = fields.Boolean(
        related='pos_invoice_journal_id.l10n_do_fiscal_journal'
    )
    pos_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='pos_config_id.pos_partner_id', 
        readonly=False
    )
