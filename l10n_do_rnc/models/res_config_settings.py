# -*- coding: utf-8 -*-

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


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rnc_service = fields.Selection(
            [('dgii', 'DGII'), ('jenrax', 'Jenrax')],
            string='Service to use',
            help='Service to use to generate the RNC, you can use DGII or Jenrax',
            default='dgii',
            config_parameter='l10n_do_rnc.rnc_service',
        )
    
    api_key = fields.Char(
        string='API Key',
        help='API Key to use when using Jenrax service',
        config_parameter='l10n_do_rnc.api_key',
    )
        