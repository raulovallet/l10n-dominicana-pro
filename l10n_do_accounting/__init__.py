from . import models
from . import wizard
from . import controllers

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def delete_views(cr, registry):
    """
    This script maps and migrate data from v12 ncf_manager module to their
    homologue fields present in this module.

    Notice: this script won't convert your v12 database to a v13 one. This script
    only works if your database have been migrated by Odoo
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    to_delete = env['ir.ui.view'].browse(3408)
    
    if to_delete:
        to_delete.unlink()
    _logger.info('View 3408')