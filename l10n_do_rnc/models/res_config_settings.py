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
        )
    
    api_key = fields.Char(
        string='API Key',
        help='API Key to use when using Jenrax service',
    )
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('l10n_do_rnc.rnc_service', self.rnc_service)
        self.env['ir.config_parameter'].sudo().set_param('l10n_do_rnc.api_key', self.api_key)
    
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        rnc_service = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_do_rnc.rnc_service', default=False)
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_do_rnc.api_key', default=False)
        res.update(
            rnc_service=rnc_service,
            api_key=api_key
        )
        return res
        