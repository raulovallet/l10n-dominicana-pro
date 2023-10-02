import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    account_moves = env['account.move'].search([
        ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'))
    ])
    
    for account_move in account_moves:
        fiscal_type_id = env['account.fiscal.type'].search([
            ('prefix', '=', account_move.l10n_latam_document_type_id.doc_code_prefix),
            ('type', '=', account_move.move_type)
        ], limit=1)
        account_move.write({
            'fiscal_type_id': fiscal_type_id.id if fiscal_type_id else False
        })
    
    
    account_moves._compute_is_l10n_do_fiscal_invoice()
    _logger.info('############## POS script executed successfully l10n_do_accounting ##############')
