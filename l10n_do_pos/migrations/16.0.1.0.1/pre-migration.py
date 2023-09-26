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
-- Obtener todas las vistas con la clave que contiene 'l10n_do_accounting'
WITH recursive dependent_views AS (
    SELECT v.id AS view_id, v.name AS view_name, v.model AS model_name
    FROM ir_ui_view v
    WHERE v.key LIKE '%l10n_do_pos%'
    UNION ALL
    SELECT v2.id AS view_id, v2.name AS view_name, v2.model AS model_name
    FROM ir_ui_view v1
    JOIN ir_ui_view v2 ON v2.inherit_id = v1.id
)
-- Eliminar las vistas y las relaciones de herencia
DELETE FROM ir_ui_view WHERE id IN (SELECT view_id FROM dependent_views);

    """)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'l10n_do_accounting';")    
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_latam_document_number TO ncf;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN ncf_expiration_date TO ncf;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_do_origin_ncf TO ncf_origin_out;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_latam_document_number TO ncf;")

    
    _logger.info('############## Pre script executed successfully l10n_do_accounting views deleted. ##############')
