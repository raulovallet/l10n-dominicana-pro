from odoo import models, fields, api, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_invoice_receivable_lines(self, data):
        if self.config_id.l10n_do_fiscal_journal:
            data.update({
                'combine_invoice_receivable_lines': {},
                'split_invoice_receivable_lines': {},
            })
            return data
        return super(PosSession, self)._create_invoice_receivable_lines(data)

    def _create_bank_payment_moves(self, data):
        if self.config_id.l10n_do_fiscal_journal:
            data.update({
                'payment_method_to_receivable_lines': {},
                'payment_to_receivable_lines': {},
            })
            return data
        return super(PosSession, self)._create_bank_payment_moves(data)

    def _create_cash_statement_lines_and_cash_move_lines(self, data):
        if self.config_id.l10n_do_fiscal_journal:
            AccountMoveLine = self.env['account.move.line']
            data.update({
                'split_cash_receivable_lines': AccountMoveLine,
                'split_cash_statement_lines': AccountMoveLine,
                'combine_cash_receivable_lines': AccountMoveLine,
                'combine_cash_statement_lines': AccountMoveLine
            })
            return data
        return super(PosSession, self)._create_cash_statement_lines_and_cash_move_lines(data)

    def _loader_params_account_fiscal_type(self):
        return {
            'search_params': {
                'domain': [('active', '=', True), ('type', 'in', ('out_invoice', 'out_refund'))],
                'fields': [
                    'name', 'requires_document', 'fiscal_position_id', 'prefix', 'type'
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

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('is_credit_note')
        return result

    def _loader_params_account_tax(self):
        result = super()._loader_params_account_tax()
        result['search_params']['fields'].append('tax_group_id')
        return result
