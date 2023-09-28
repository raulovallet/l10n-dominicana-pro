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
    views_count = 1
    while views_count > 0:
        views = env['ir.ui.view'].search([
            ('inherit_children_ids', '=', False),
            ('id', 'in', env['ir.model.data'].search([
                ('model', '=', 'ir.ui.view'),
                ('module', 'in', ['l10n_do_pos'])]).mapped('res_id')
            )        
        ])
        _logger.info(views)
        views_count = len(views)
        views.unlink()

    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'l10n_do_pos';")    
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_latam_document_number TO ncf;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_do_ncf_expiration_date TO ncf_expiration_date;")
    cr.execute("ALTER TABLE pos_order RENAME COLUMN l10n_do_origin_ncf TO ncf_origin_out;")
    
    _logger.info('############## Pre script executed successfully l10n_do_pos views deleted. ##############')