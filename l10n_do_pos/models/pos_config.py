from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


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
    l10n_do_type_limit_order_history = fields.Selection(
        selection=[
            ('all', 'All orders'),
            ('days', 'Days'),
        ],
        string='Limit order history',
        default='all',
        help="""
        This field allows you to limit the number of orders that are showed in the POS:
            - All orders: All orders will be showed.
            - Days: Only the orders of the amount of day will be showed.
        """,
    )
    l10n_do_type_limit_order_history_days = fields.Integer(
        string='Days',
        default=30,
    )

    @api.constrains('l10n_do_type_limit_order_history_days')
    def _check_l10n_do_type_limit_order_history(self):
        for record in self:
            if record.l10n_do_type_limit_order_history == 'days' and record.l10n_do_type_limit_order_history_days <= 0:
                raise ValidationError(_('The days must be greater than 0'))
