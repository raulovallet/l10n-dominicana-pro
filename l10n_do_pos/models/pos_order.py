import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    ncf = fields.Char(
        string='NCF',
        copy=False,
    )
    ncf_origin_out = fields.Char(
        string='Affects',
        copy=False,
    )
    ncf_expiration_date = fields.Date(
        string='NCF expiration date',
    )
    fiscal_type_id = fields.Many2one(
        string='Fiscal type',
        comodel_name='account.fiscal.type',
    )
    fiscal_sequence_id = fields.Many2one(
        string='Fiscal Sequence',
        comodel_name='account.fiscal.sequence',
        copy=False,
    )
    is_used_in_order = fields.Boolean(
        default=False
    )

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result['ncf'] = order.ncf
        result['ncf_origin_out'] = order.ncf_origin_out
        result['ncf_expiration_date'] = order.ncf_expiration_date
        result['fiscal_type_id'] = order.fiscal_type_id.id if order.fiscal_type_id else False
        result['fiscal_sequence_id'] = order.fiscal_sequence_id.id if order.fiscal_sequence_id else False
        return result

    @api.model
    def _order_fields(self, ui_order):
        """
        Prepare the dict of values to create the new pos order.
        """
        fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('ncf', False):
            fields['ncf'] = ui_order['ncf']
            fields['ncf_origin_out'] = ui_order['ncf_origin_out']
            fields['ncf_expiration_date'] = ui_order['ncf_expiration_date']
            fields['fiscal_type_id'] = ui_order['fiscal_type_id']
            fields['fiscal_sequence_id'] = ui_order['fiscal_sequence_id']

        return fields

    def _prepare_invoice_vals(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()

        if self.config_id.invoice_journal_id.l10n_do_fiscal_journal:
            invoice_vals['ref'] = self.ncf
            invoice_vals['origin_out'] = self.ncf_origin_out
            invoice_vals['ncf_expiration_date'] = self.ncf_expiration_date
            invoice_vals['fiscal_type_id'] = self.fiscal_type_id.id
            invoice_vals['fiscal_sequence_id'] = self.fiscal_sequence_id.id

        return invoice_vals

    # @api.model
    # def _payment_fields(self, ui_paymentline):
    #     """
    #     This part is for credit note.
    #     """
    #     fields = super(PosOrder, self)._payment_fields(ui_paymentline)
    #     fields.update({'note': ui_paymentline.get('returned_ncf')})
    #     return fields

    # def _prepare_bank_statement_line_payment_values(self, data):
    #     """
    #     This part is for credit note.
    #     """
    #     args = super(PosOrder, self)._prepare_bank_statement_line_payment_values(data)
    #     if 'note' in data:
    #         args.update({'note': data['note']})
    #     return args

    
    def _create_order_payments(self):
        """
        Create all orders payment from statements
        :return:
        """
        for order in self:
            if order.config_id.invoice_journal_id.l10n_do_fiscal_journal:
                pass
                # for statement in order.statement_ids:
                #     # This part is for return order (credits notes)
                #     if statement.journal_id.is_for_credit_notes:
                #         # Note in statement line is equals to returned_ncf
                #         # (NCF credit note)
                #         credit_note_order = self.env['pos.order']\
                #             .search([('ncf', '=', statement.note)])
                #         if not credit_note_order:
                #             raise UserError(_('Credit note not exist'))

                #         if credit_note_order.invoice_id.state == 'paid':
                #             raise UserError(
                #                 _('The credit note used in another invoice,'
                #                   ' please unlink that invoice.')
                #             )
                #         credit_note_order.update({
                #             'is_used_in_order': True
                #         })
                #         lines = credit_note_order.invoice_id.move_id.line_ids
                #         statement.write({
                #             'move_name': credit_note_order.invoice_id.move_name,
                #             'journal_entry_ids': [(4, x) for x in lines.ids]
                #         })
                #         order._reconcile_refund_invoice(
                #             credit_note_order.invoice_id
                #         )
                #     else:
                #         statement.sudo().fast_counterpart_creation()

                #     if not statement.journal_entry_ids.ids:
                #         raise UserError(
                #             _('All the account entries lines must be processed'
                #               ' in order to close the statement.')
                #         )

    def action_pos_order_invoice_no_return_pdf(self):
        """
        Create invoice on background
        :return:
        """
        invoice = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            local_context = dict(
                self.env.context,
                force_company=order.company_id.id,
                company_id=order.company_id.id)

            if order.account_move:
                invoice += order.account_move
                continue

            if not order.partner_id:
                
                if not order.config_id.pos_partner_id:
                    raise UserError(_('This point of sale not have default customer, please set default customer in config POS'))
                
                order.write({
                    'partner_id': order.config_id.pos_partner_id.id
                })

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()
            payment_moves = order._apply_invoice_payments()

    # @api.model
    # def _process_order(self, order, draft, existing_order):
    #     """
    #     this part is using for eliminate cash return
    #     :param pos_order:
    #     :return pos_order:
    #     """
    #     if pos_order['amount_return'] > 0:

    #         pos_session_obj = self.env['pos.session'].browse(
    #             pos_order['pos_session_id']
    #         )
    #         cash_journal_id = pos_session_obj.cash_journal_id.id
    #         if not cash_journal_id:
    #             # If none, select for change one of the cash journals of the PO
    #             # This is used for example when a customer pays by credit card
    #             # an amount higher than total amount of the order and gets cash
    #             # back
    #             cash_journal = [statement.journal_id
    #                             for statement in pos_session_obj.statement_ids
    #                             if statement.journal_id.type == 'cash']
    #             if not cash_journal:
    #                 raise UserError(
    #                     _("No cash statement found for this session. "
    #                       "Unable to record returned cash."))

    #             cash_journal_id = cash_journal[0].id

    #         for index, statement in enumerate(pos_order['statement_ids']):

    #             if statement[2]['journal_id'] == cash_journal_id:
    #                 pos_order['statement_ids'][index][2]['amount'] = \
    #                     statement[2]['amount'] - pos_order['amount_return']

    #         pos_order['amount_return'] = 0

    #     return super(PosOrder, self)._process_order(pos_order)

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            
            if order.config_id.invoice_journal_id.l10n_do_fiscal_journal \
                    and order.state != 'invoiced' \
                    and order.amount_total != 0 \
                    and order.ncf:
                order.action_pos_order_invoice_no_return_pdf()
                # if order._should_create_picking_real_time():
                #     self._create_order_picking()

        return order_ids

    def _reconcile_refund_invoice(self, refund_invoice):
        """
        For returns orders (nota de credito)
        :param refund_invoice:
        """
        invoice = self.invoice_id
        movelines = invoice.move_id.line_ids
        to_reconcile_ids = {}
        to_reconcile_lines = self.env['account.move.line']
        for line in movelines:
            if line.account_id.id == invoice.account_id.id:
                to_reconcile_lines += line
                to_reconcile_ids.setdefault(line.account_id.id, []).append(
                    line.id)
            if line.reconciled:
                line.remove_move_reconcile()
        for tmpline in refund_invoice.move_id.line_ids:
            if tmpline.account_id.id == invoice.account_id.id:
                to_reconcile_lines += tmpline
        to_reconcile_lines.filtered(lambda l: not l.reconciled).reconcile()


    def get_next_fiscal_sequence(
            self, 
            fiscal_type_id,
            company_id, 
            payments
        ):
        """
        search active fiscal sequence dependent with fiscal type
        :param order:[fiscal_type_id, company_id, mode, lines,]
        :return: {ncf, expiration date, fiscal sequence}
        """
        fiscal_type = self.env['account.fiscal.type'].search([
            ('id', '=', fiscal_type_id)
        ])

        if not fiscal_type:
            raise UserError(_('Fiscal type not found'))

        for payment in payments:
            if payment.get('returned_ncf', False):
                cn_invoice = self.env['account.move'].search([
                    ('ref', '=', payment['returned_ncf']),
                    ('type', '=', 'out_refund'),
                    ('is_l10n_do_fiscal_invoice', '=', True),
                ])
                if cn_invoice.residual != cn_invoice.amount_total:
                    raise UserError(
                        _('This credit note (%s) has been used' % payment['returned_ncf'])
                    )

        fiscal_sequence = self.env['account.fiscal.sequence'].search([
            ('fiscal_type_id', '=', fiscal_type.id),
            ('state', '=', 'active'),
            ('company_id', '=', company_id)
        ], limit=1)

        if not fiscal_sequence:
            raise UserError(_(u"There is no current active NCF of {}"
                              u", please create a new fiscal sequence "
                              u"of type {}.").format(
                fiscal_type.name,
                fiscal_type.name,
            ))

        return {
            'ncf': fiscal_sequence.get_fiscal_number(),
            'fiscal_sequence_id': fiscal_sequence.id,
            'ncf_expiration_date': fiscal_sequence.expiration_date
        }

    def get_credit_note(self, ncf):
        """
        Get credit note
        :param ncf:
        :return:
        """
        credit_note = self.env['account.move'].search([
            ('ref', '=', ncf),
            ('move_type', '=', 'out_refund'),
            ('is_l10n_do_fiscal_invoice', '=', True),
        ], limit=1)

        if not credit_note:
            raise UserError(_('Credit note not found'))

        return {
            'partner_id': credit_note.partner_id.id,
            'residual_amount': credit_note.amount_residual,
        }