# -*- coding: utf-8 -*-
# Modified by jenrax SRL on 2025-01-30
# copyright (c) 2025 jenrax SRL
# All Rights Reserved

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

import logging
import json
import re
import requests
_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(str(err))

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to automatically fetch the company name
        based on the RNC (Dominican Tax ID) provided in the 'vat' or 'name' field.
        """
        for val in vals_list:
            rnc_value = val.get('vat') or val.get('name')
            rnc_value = rnc_value.replace('-', '') if rnc_value else None

            if rnc_value and rnc_value.isdigit() and not val.get('vat'):
                val['vat'] = rnc_value

            if val.get('country_id') == self.env.ref('base.do').id and rnc_value and rnc_value.isdigit():
                contact_exist = self.env['res.partner'].search([('vat', '=', rnc_value)], limit=1)
                if contact_exist:
                    raise UserError(_('The contact %s already exists with the %s: %s.') % 
                                    (contact_exist.name, _('ID') if len(rnc_value) == 11 else _('RNC'), rnc_value))

                try:
                    name = self.get_name_from_dgii(rnc_value)
                    if name:
                        val.update({'name': name, 'vat': rnc_value})
                    elif not name:
                        raise UserError(_(
                            'This RNC or Cedula (%s) could not be found, please confirm the RNC or Cedula number. '
                            'If it is a system search error, enter manually the full company name and the RNC / Cedula '
                            'in the field labeled RNC for companies and Cedula for individuals to force create the contact.'
                        ) % rnc_value)

                except Exception as e:
                    raise ValidationError(e)

        res = super(Partner, self).create(vals_list)
        res._compute_sale_fiscal_type_id()
        return res

    def write(self, vals):
        """
        Override the write method to validate RNC/Cedula when updating the partner.
        """
        if 'vat' in vals:
            rnc_value = vals.get('vat').replace('-', '') if vals.get('vat') else None
            if rnc_value and rnc_value.isdigit():
                existing_partner = self.env['res.partner'].search([('vat', '=', rnc_value), ('id', '!=', self.id)], limit=1)
                if existing_partner:
                    raise UserError(_('The contact %s already exists with the %s: %s.') % 
                                    (existing_partner.name, _('ID') if len(rnc_value) == 11 else _('RNC'), rnc_value))
        
        res = super(Partner, self).write(vals)
        return res
   
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

        rnc_service = self.env['ir.config_parameter'].sudo().get_param('l10n_do_rnc.rnc_service', default='dgii')

        if rnc_service == 'dgii':
            result = rnc.check_dgii(vat)
            if result is not None:
                result["name"] = " ".join(re.split(r"\s+", result["name"], flags=re.UNICODE))
                return result["name"]

        elif rnc_service == 'jenrax':
            
            api_key = self.env['ir.config_parameter'].sudo().get_param('l10n_do_rnc.api_key', default=False)
        
            if not api_key:
                raise UserError(_('API Key is not configured.Please contact your administrator at number XXXXXXXX'))

            _logger.info(f"API Key: {api_key}")

            if not rnc:
                raise UserError(_('Please provide a valid RNC or Cedula.'))

            try:
                payload = {'rnc': vat}
            
                headers = {
                    'Authorization': f'{api_key}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                _logger.info(f"Sending request to API with payload: {payload} and headers: {headers}")

                response = requests.post('http://localhost:8000/rnc/', 
                                    data=payload, headers=headers)

                _logger.info(f"API response: {response.status_code} - {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    _logger.info(f"Data received: {data}")
                    if data.get('results'):
                        return data['results'][0].get('name', False)
                    else:
                        return False

                else:
                    _logger.error(f"Error querying the API. Code: {response.status_code} - {response.text}")
                    raise UserError(_('Could not retrieve RNC information. Please check the API.'))

            except requests.RequestException as e:
                _logger.error(f"API connection error: {e}")
                raise UserError(_('Error connecting to the RNC API. Please ensure the service is running.'))

        return False