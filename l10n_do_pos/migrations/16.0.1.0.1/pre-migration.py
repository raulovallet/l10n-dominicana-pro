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

    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE id IN (
        SELECT ir_ui_view.id
        FROM ir_ui_view
        JOIN ir_model_data ON ir_ui_view.id = ir_model_data.res_id
        WHERE ir_ui_view.inherit_id IS NOT NULL
        AND ir_model_data.module = 'l10n_do_pos'
        );
        DELETE FROM ir_ui_view
        WHERE id IN (
        SELECT ir_ui_view.id
        FROM ir_ui_view
        JOIN ir_model_data ON ir_ui_view.id = ir_model_data.res_id
        WHERE ir_ui_view.inherit_id IS NOT NULL
        AND ir_model_data.module = 'l10n_do_pos'
        );
    """)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'l10n_do_accounting';")    
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_latam_document_number TO ncf;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN ncf_expiration_date TO ncf;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_do_origin_ncf TO ncf_origin_out;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_latam_document_number TO ncf;")

    
    _logger.info('############## Pre script executed successfully l10n_do_accounting views deleted. ##############')
