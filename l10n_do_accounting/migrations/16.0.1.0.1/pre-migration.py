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

    cr.execute("DELETE FROM ir_ui_view WHERE id = 3408;")
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE id IN (
        SELECT ir_ui_view.id
        FROM ir_ui_view
        JOIN ir_model_data ON ir_ui_view.id = ir_model_data.res_id
        WHERE ir_ui_view.inherit_id IS NOT NULL
        AND ir_model_data.module = 'l10n_do_accounting'
        );
        DELETE FROM ir_ui_view
        WHERE id IN (
        SELECT ir_ui_view.id
        FROM ir_ui_view
        JOIN ir_model_data ON ir_ui_view.id = ir_model_data.res_id
        WHERE ir_model_data.module = 'l10n_do_accounting'
        );
    """)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'l10n_latam.document.type' AND module = 'l10n_do_accounting';")    
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'l10n_do_accounting';")    
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_expense_type TO expense_type;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_ncf_expiration_date TO ncf_expiration_date;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_cancellation_type TO annulation_type;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_origin_ncf TO origin_out;")
    cr.execute("ALTER TABLE account_move RENAME COLUMN l10n_do_income_type TO income_type;")
    cr.execute("UPDATE account_move SET ref = name where move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund');")


    cr.execute("""
-- Obtener todas las vistas con claves que contienen los valores de la lista
WITH recursive dependent_views AS (
    SELECT v.id AS view_id, v.name AS view_name, v.model AS model_name
    FROM ir_ui_view v
    WHERE v.key LIKE ANY (ARRAY['%pos_auto_ship_later%', 
                                '%l10n_do_e_accounting%', 
                                '%generic_discount_limit%',
                                '%account_margin%',
                                '%mass_editing%',
                                '%theme_prime%',
                                '%droggol_theme_common%',
                                '%invoice_payment_to%',
                                '%l10n_do_rnc_search%',
                                '%pos_discount_limit%'])
    UNION ALL
    SELECT v2.id AS view_id, v2.name AS view_name, v2.model AS model_name
    FROM ir_ui_view v1
    JOIN ir_ui_view v2 ON v2.inherit_id = v1.id
)
-- Eliminar las vistas y las relaciones de herencia
DELETE FROM ir_ui_view WHERE id IN (SELECT view_id FROM dependent_views);
""")
    
    # env['ir.module.module'].search([('name', '=', 'dgii_reports')]).button_immediate_install()

    modules = env['ir.module.module'].search([
        ('state', '=', 'installed'), 
        ('name', 'in', (
            'account_margin', 
            'invoice_payment_to', 
            'l10n_do_e_accounting', 
            'l10n_do_rnc_search', 
            'mass_editing', 
            'pos_auto_ship_later', 
            'pos_discount_limit', 
            'theme_prime',
            'l10n_do_accounting_report',
        ))
    ])

    for module in modules:
        try:
            module.button_immediate_uninstall()
        except Exception as e:
            print(e)

    second_modules = env['ir.module.module'].search([
        ('state', '=', 'installed'), 
        ('name', 'in', (
                'droggol_theme_common',
                'generic_discount_limit',
                'l10n_do_accounting_report',
                # 'l10n_do_accounting',
            )
        )
    ]) 

    for module in second_modules:
        try:
            module.button_immediate_uninstall()
        except Exception as e:
            print(e)
    
    _logger.info('############## Pre script executed successfully l10n_do_accounting views deleted. ##############')
