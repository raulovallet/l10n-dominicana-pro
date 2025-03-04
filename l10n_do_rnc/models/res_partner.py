# -*- coding: utf-8 -*-
# Modified by jenrax SRL on 2025-01-30
# copyright (c) 2025 jenrax SRL
# All Rights Reserved

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base_vat.models.res_partner import _ref_vat

if _ref_vat:
    _ref_vat.update({
        'do': _("Example: '22400504056' or '133195593' (format: 9 digits for RNC or 11 Digits for Cedula, all numbers.)"),
    })

import logging
import re
import requests
_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(str(err))



class Partner(models.Model):
    _inherit = 'res.partner'
    
    def check_vat_do(self, vat):
        return rnc.is_valid(vat) or cedula.is_valid(vat)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            is_from_vat = val.get('vat', False)

            rnc = val.get('vat', '') if is_from_vat else val.get('name', '')
            rnc = rnc.replace('-', '') if rnc else rnc

            if val.get('country_id', False) == self.env.ref('base.do').id and rnc and rnc.isdigit():
                
                contact_exist = self.env['res.partner'].search([
                    ('vat', '=', rnc),
                    ('company_id', 'in', (val.get('company_id', False), False))
                ], limit=1)
                
                if contact_exist:
                    raise UserError(_('The contact %s already exists with the %s: %s.') % (contact_exist.name, _('ID') if len(rnc) == 11 else _('RNC'), rnc))
                
                try:
                    name = self.get_name_from_dgii(rnc)
                    
                    if name:
                        val.update({
                            'name': name,
                            'vat': rnc
                        })

                    elif not name and val.get('vat', False):

                        raise UserError(_(
                            'This RNC or Cedula (%s) could not be found, please confirm the RNC or Cedula number.\
                            If it is a system search error, enter manually the full company name and the RNC / Cedula \
                            in the field labeled RNC for companies and Cedula for individuals for force create the contact.'
                        ) % (rnc))
                        
                except Exception as e:
                    
                    if not is_from_vat:
                        raise ValidationError(e)
                    
                    _logger.error(e)

        res = super(Partner, self).create(vals_list)

        res._compute_sale_fiscal_type_id()
        
        return res

    def write(self, vals):

        if vals.get('vat', False):
            dominican_company_parnters = self.filtered(
                lambda p: p.country_id and p.country_id.code == 'DO' and not p.parent_id)
                
            for partner in dominican_company_parnters:

                try:
                    name = self.get_name_from_dgii(vals['vat'])

                    if name:
                        vals['name'] = name

                except Exception as e:
                    _logger.error(e)

        return super(Partner, self).write(vals)

    def get_name_from_dgii(self, vat):
        """
        Retrieves the company name based on the configured service (DGII or Jenrax).
        :param vat: RNC or ID to query.
        :return: Company name or False if not found.
        """
        if len(vat) not in [9, 11]:
            raise UserError(_('Please verify the RNC/ID. It must have 9 digits for RNC or 11 for ID.'))

        if not ((len(vat) == 9 and rnc.is_valid(vat)) or (len(vat) == 11 and cedula.is_valid(vat))):
            raise UserError(_('The entered RNC/ID is not valid.'))

        rnc_service = self.env['ir.config_parameter'].sudo().get_param('l10n_do_rnc.l10n_do_rnc_service', default='dgii')

        if rnc_service == 'dgii':
            result = rnc.check_dgii(vat)
            if result is not None:
                result["name"] = " ".join(re.split(r"\s+", result["name"], flags=re.UNICODE))
                return result["name"]

        elif rnc_service == 'jenrax':
            
            jenrax_api_key = self.env['ir.config_parameter'].sudo().get_param('l10n_do_rnc.l10n_do_rnc_jenrax_api_key', default=False)
        
            if not jenrax_api_key:
                raise UserError(
                    _('API Key is not configured. Please go to https://jenrax.com to get your API Key.'))

            if not vat:
                raise UserError(_('Please provide a valid RNC or Cedula.'))
                
            try:
                if not self.env.company.vat:
                    raise UserError(_('Please configure the company VAT in the company settings for %s.') % self.env.company.name)

                url = f"https://rnc.jenrax.com/search?rnc={vat}&user_id={self.env.company.vat}"
                headers = {
                    'X-API-KEY': jenrax_api_key
                }
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    return data.get('name', False)

                else:
                    _logger.error(f"Error querying the API. Code: {response.status_code} - {response.text}")
                    raise UserError(_('Could not retrieve RNC information from the API.'))

            except requests.RequestException as e:
                _logger.error(f"API connection error: {e}")
                raise UserError(_('Error connecting to the Jenrax RNC API.'))

        return False
