##############################################################################
#
#    Developed by Jenrax Srl.
#    Modified by Raul Ovalle, Gerardo Alí Ferraro Schelijasch.
#    Creation Date: 2025-01-30
#    Version: 1.0.0
#
#    Copyright (c) Jenrax Srl. All Rights Reserved.
#    This software is protected by copyright law and international treaties.
#    Unauthorized reproduction or distribution of this program, or any portion
#    of it, may result in severe civil and criminal penalties, and will be
#    prosecuted to the maximum extent possible under the law.
#
##############################################################################

from odoo import models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_do_rnc_service = fields.Selection(
        selection=[
            ('dgii', 'DGII'), 
            ('jenrax', 'Jenrax')
        ],
        string='Service to use',
        help='Service to use to generate the RNC, you can use DGII or Jenrax',
        default='dgii',
        config_parameter='l10n_do_rnc.l10n_do_rnc_service',
        required=True
    )
    
    l10n_do_rnc_jenrax_api_key = fields.Char(
        string='Jenrax RNC API key',
        help='API key for accessing the Jenrax RNC service',
        config_parameter='l10n_do_rnc.l10n_do_rnc_jenrax_api_key',
    )
        