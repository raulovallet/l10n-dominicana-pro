from odoo import models, fields, api, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_account_fiscal_type(self):
        return {
            'search_params': {
                'domain': [('active', '=', True), ('type', '=', 'out_invoice')],
                'fields': [
                    'name', 'requires_document', 'fiscal_position_id', 'prefix'
                ],
            },
        }

    def _get_pos_ui_account_fiscal_type(self, params):
        return self.env['account.fiscal.type'].sudo().search_read(**params['search_params'])

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result.append('account.fiscal.type')
        return result

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        
        result['search_params']['fields'].append('sale_fiscal_type_id')
        
        return result
