import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Maybe not necessary
    # pos_orders = env['pos.order'].search([])
    
    # for pos_order in pos_orders:
    #     fiscal_type_id = env['account.fiscal.type'].search([
    #         ('prefix', '=', pos_order.l10n_latam_document_type_id.doc_code_prefix),
    #         ('type', 'in', ('out_invoice', 'out_refund'))
    #     ], limit=1)
    #     pos_order.write({
    #         'fiscal_type_id': fiscal_type_id.id if fiscal_type_id else False
    #     })

    _logger.info('############## Pre script executed successfully l10n_do_accounting views deleted. ##############')