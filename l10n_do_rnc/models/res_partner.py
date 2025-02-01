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
        for val in vals_list:
            is_from_vat = val.get('vat', False)

            rnc = val.get('vat', '') if is_from_vat else val.get('name', '')
            rnc = rnc.replace('-', '') if rnc else rnc

            if val.get('country_id', False) == self.env.ref('base.do').id and rnc and rnc.isdigit():
                contact_exist = self.env['res.partner'].search([('vat', '=', rnc)], limit=1)
                
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
        if (len(vat) not in [9, 11]):
            raise UserError(_('Please check the RNC/Cedula, it does not have the appropriate number of digits, only enter numbers (without hyphens), 9 digits for RNC and 11 digits for Cedula.'))
            
        elif (not ((len(vat) == 9 and rnc.is_valid(vat)) or (len(vat) == 11 and cedula.is_valid(vat)))):
            raise UserError(_('Check RNC/Cedula, seems like it is not correct'))
        
        else:
            result = rnc.check_dgii(vat)
            if result is not None:
                # remove all duplicate white space from the name
                result["name"] = " ".join(
                    re.split(r"\s+", result["name"], flags=re.UNICODE))
                
                return result["name"]
        
        return False



    def get_name_from_jenrax_l10n_do_rnc_service(self):
        self.ensure_one()

        rnc = "133195593"  # Puedes hacer este valor dinámico si lo necesitas

        if not rnc:
            raise UserError(_('Por favor, proporcione un RNC o Cédula válido.'))

        try:
            # Hacer la solicitud HTTP GET a la API
            response = requests.get(f'http://localhost:8000/rnc/?rnc={rnc}')

            # Verificar si la respuesta es exitosa (código 200)
            if response.status_code == 200:
                data = response.json()
                _logger.info(f"Respuesta de la API: {data}")
                raise UserError(f'{data}')

            else:
                _logger.error(f"Error al consultar la API. Código: {response.status_code} - {response.text}")
                raise UserError(_('No se pudo obtener información del RNC. Verifique la API.'))

        except requests.RequestException as e:
            _logger.error(f"Error de conexión con la API: {e}")
            raise UserError(_('Error de conexión con la API de RNC. Verifique que el servicio está en ejecución.'))