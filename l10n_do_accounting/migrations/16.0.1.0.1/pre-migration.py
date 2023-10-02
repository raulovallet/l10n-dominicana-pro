import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    This script maps and migrate data from v12 ncf_manager module to their
    homologue fields present in this module.

    Notice: this script won't convert your v12 database to a v13 one. This script
    only works if your database have been migrated by Odoo
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # cr.execute("DELETE FROM ir_ui_view WHERE id = 3408;")
    views_count = 1
    while views_count > 0:
        views = env['ir.ui.view'].search([
            ('inherit_children_ids', '=', False),
            '|',
            ('id', 'in', env['ir.model.data'].search([
                ('inherit_children_ids', '=', False),
                ('model', '=', 'ir.ui.view'),
                ('module', 'in', [
                    'l10n_do_accounting',
                    'pos_auto_ship_later', 
                    'l10n_do_e_accounting', 
                    'generic_discount_limit',
                    'account_margin',
                    'mass_editing',
                    'theme_prime',
                    'droggol_theme_common',
                    'invoice_payment_to',
                    'l10n_do_rnc_search',
                    'pos_discount_limit',
                    'l10n_do_accounting_report'
                ])]).mapped('res_id')
            ),    
            ('key', 'like', '%theme_prime%')
        ])
        views_count = len(views)
        views.unlink()

    cr.execute("DELETE FROM ir_model_data WHERE model = 'l10n_latam.document.type' AND module = 'l10n_do_accounting';")    
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'l10n_do_accounting';")    
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_expense_type TO expense_type;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_ncf_expiration_date TO ncf_expiration_date;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_cancellation_type TO annulation_type;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_origin_ncf TO origin_out;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_income_type TO income_type;")
    cr.execute("ALTER TABLE res_partner RENAME COLUMN l10n_do_expense_type TO expense_type;")
    cr.execute("UPDATE account_move SET ref = name where move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund');")
    
    _logger.info('############## Pre script executed successfully l10n_do_accounting views deleted. ##############')
