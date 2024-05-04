# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.

import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvoiceServiceTypeDetail(models.Model):
    _name = 'invoice.service.type.detail'
    _description = "Invoice Service Type Detail"

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ('code_unique', 'unique(code)', _('Code must be unique')),
    ]


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def _get_invoice_payment_widget(self):                    
        return self.invoice_payments_widget.get('content', []) if self.invoice_payments_widget else []

    @api.depends('payment_state', 'invoice_date', 'invoice_payments_widget')
    def _compute_invoice_payment_date(self):
        for inv in self:
            payment_date = False
            
            if inv.payment_state in ('paid', 'in_payment'):
                dates = [
                    payment['date'] for payment in inv._get_invoice_payment_widget()
                ]
                if dates:
                    max_date = max(dates)
                    invoice_date = inv.invoice_date
                    payment_date = max_date if max_date >= invoice_date \
                        else invoice_date

            inv.payment_date = payment_date

    @api.constrains('line_ids',  'line_ids.tax_line_id')
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice"""
        for inv in self:
            line = [
                tax_line.tax_line_id.l10n_do_tax_type
                for tax_line in inv._get_tax_line_ids()
                if tax_line.tax_line_id.l10n_do_tax_type in ['isr', 'ritbis']
            ]
            if len(line) != len(set(line)):
                raise ValidationError(_('An invoice cannot have multiple withholding taxes.'))

    def _convert_to_local_currency(self, amount):
        sign = -1 if self.move_type in ['in_refund', 'out_refund'] else 1
        if self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.invoice_date)
            round_curr = currency_id.round
            amount = round_curr(currency_id._convert(amount, self.company_id.currency_id, self.company_id, self.invoice_date))

        return amount * sign

    def _get_tax_line_ids(self):
        return self.line_ids.filtered(lambda l: l.tax_line_id)

    @api.depends(
        'state', 
        'line_ids', 
        'line_ids.balance', 
        'line_ids.tax_line_id'
    )
    def _compute_taxes_fields(self):
        
        """Compute invoice common taxes fields"""
        
        for inv in self:

            inv.invoiced_itbis = 0
            inv.selective_tax = 0
            inv.other_taxes = 0
            inv.legal_tip = 0
            inv.advance_itbis = 0
            
            inv.cost_itbis = 0
            inv.proportionality_tax = 0
            
            tax_line_ids = inv._get_tax_line_ids()
            
            if inv.state != 'draft' and tax_line_ids:
                
                # Taxes
                inv.invoiced_itbis = abs(sum(tax_line_ids.filtered(
                    lambda tax: tax.tax_line_id.l10n_do_tax_type == 'itbis').mapped('balance')
                ))
                inv.selective_tax = abs(sum(tax_line_ids.filtered(
                    lambda tax: tax.tax_line_id.l10n_do_tax_type == 'isc').mapped('balance')
                ))
                inv.other_taxes = abs(sum(
                    tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.l10n_do_tax_type == 'other').mapped('balance')
                ))
                inv.legal_tip = abs(sum(
                    tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.l10n_do_tax_type == 'tip').mapped('balance')
                ))

                # TODO: investigate Subject to proportionality and ITBIS carried to cost
                # inv.cost_itbis = abs(sum(
                #     tax_line_ids.filtered(
                #         lambda tax: tax.tax_line_id.l10n_do_tax_type == 'itbis_cost').mapped('balance')
                # ))
                # inv.proportionality_tax = abs(sum(
                #     tax_line_ids.filtered(
                #         lambda tax: tax.tax_line_id.l10n_do_tax_type == 'prop').mapped('balance')
                # ))
                inv.advance_itbis = inv.invoiced_itbis - inv.cost_itbis

    @api.depends(
        'state', 
        'payment_state',
        'line_ids', 
        'line_ids.balance', 
        'line_ids.tax_line_id'
    )
    def _compute_withholding_taxes(self):

        # Withholdings
        
        for inv in self:
            tax_line_ids = inv._get_tax_line_ids()
            
            inv.withholding_itbis = 0
            inv.income_withholding = 0
            
            if inv.payment_state in ('paid', 'in_payment') and tax_line_ids and inv.state != 'draft':

                inv.withholding_itbis = abs(sum(
                    tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.l10n_do_tax_type == 'ritbis').mapped('balance')
                ))

                inv.income_withholding = abs(sum(
                    tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.l10n_do_tax_type == 'isr').mapped('balance')
                ))

    @api.depends(
        'state',
        'invoice_date',
        'invoice_line_ids', 
        'invoice_line_ids.product_id',
        'invoice_line_ids.price_subtotal'
    )
    def _compute_amount_fields(self):
        
        """Compute Purchase amount by product type"""
        
        for inv in self:
            service_amount = 0
            good_amount = 0
            
            if inv.state != 'draft' and inv.invoice_date:
                for line in inv.invoice_line_ids:
                    if not line.product_id:
                        service_amount += line.price_subtotal
                    
                    elif line.product_id.type in ['product', 'consu']:
                        good_amount += line.price_subtotal
                    
                    else:
                        service_amount += line.price_subtotal
                
                service_amount = inv._convert_to_local_currency(service_amount)
                good_amount = inv._convert_to_local_currency(good_amount)

            inv.service_total_amount = service_amount
            inv.good_total_amount = good_amount

    @api.depends(
        'state',
        'invoice_line_ids', 
        'invoice_line_ids.product_id', 
    )
    def _compute_isr_withholding_type(self):
        """Compute ISR Withholding Type

        Keyword / Values:
        01 -- Alquileres
        02 -- Honorarios por Servicios
        03 -- Otras Rentas
        04 -- Rentas Presuntas
        05 -- Intereses Pagados a Personas Jurídicas
        06 -- Intereses Pagados a Personas Físicas
        07 -- Retención por Proveedores del Estado
        08 -- Juegos Telefónicos
        """
        for inv in self:
            inv.isr_withholding_type = False
            
            if inv.move_type == 'in_invoice' and inv.state != 'draft':
                isr = [
                    tax_line.tax_line_id
                    for tax_line in inv._get_tax_line_ids()
                    if tax_line.tax_line_id.l10n_do_tax_type == 'isr'
                ]
                if isr:
                    inv.isr_withholding_type = isr.pop(0).isr_retention_type

    def _get_payment_string(self):
        """Compute Vendor Bills payment method string

        Keyword / Values:
        cash        -- Efectivo
        bank        -- Cheques / Transferencias / Depósitos
        card        -- Tarjeta Crédito / Débito
        credit      -- Compra a Crédito
        swap        -- Permuta
        credit_note -- Notas de Crédito
        mixed       -- Mixto
        """
        payments = []
        p_string = ""

        for payment in self._get_invoice_payment_widget():
            payment_id = self.env['account.payment'].browse(
                payment.get('account_payment_id'))
            move_id = False
            if payment_id:
                if payment_id.journal_id.type in ['cash', 'bank']:
                    p_string = payment_id.journal_id.payment_form

            if not payment_id:
                move_id = self.env['account.move'].browse(
                    payment.get('move_id'))
                if move_id:
                    p_string = 'swap'

            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id or move_id else 'credit_note'
            payments.append(payment)

        methods = {p for p in payments}
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return 'mixed'

    @api.depends('payment_state')
    def _compute_in_invoice_payment_form(self):
        for inv in self:
            if inv.payment_state in ('paid', 'in_payment'):
                payment_dict = {'cash': '01', 'bank': '02', 'card': '03',
                                'credit': '04', 'swap': '05',
                                'credit_note': '06', 'mixed': '07'}
                inv.payment_form = payment_dict.get(inv._get_payment_string())
            else:
                inv.payment_form = '04'

    @api.depends('fiscal_type_id')
    def _compute_is_exterior(self):
        for inv in self:
            inv.is_exterior = True if inv.fiscal_type_id and \
                inv.fiscal_type_id.prefix in ('B17') else False

    @api.onchange('service_type')
    def onchange_service_type(self):
        self.service_type_detail = False
        return {
            'domain': {
                'service_type_detail': [
                    ('parent_code', '=', self.service_type)
                    ]
            }
        }

    @api.onchange('journal_id')
    def ext_onchange_journal_id(self):
        self.service_type = False
        self.service_type_detail = False

    # TODO: 
    # ISR Percibido       --> Este campo se va con 12 espacios en 0 para el 606
    # ITBIS Percibido     --> Este campo se va con 12 espacios en 0 para el 606
    service_total_amount = fields.Monetary(
        string="Service Total Amount",
        compute='_compute_amount_fields',
        currency_field='company_currency_id'
    )
    good_total_amount = fields.Monetary(
        string="Good Total Amount",
        compute='_compute_amount_fields',
        currency_field='company_currency_id',
    )
    invoiced_itbis = fields.Monetary(
        string="Invoiced ITBIS",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    )
    proportionality_tax = fields.Monetary(
        string="Proportionality Tax",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    )
    cost_itbis = fields.Monetary(
        string="Cost Itbis",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    )
    advance_itbis = fields.Monetary(
        string="Advanced ITBIS",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
    )
    isr_withholding_type = fields.Char(
        string="ISR Withholding Type",
        compute='_compute_isr_withholding_type',
        size=2
    )
    selective_tax = fields.Monetary(
        string="Selective Tax",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    )
    other_taxes = fields.Monetary(
        string="Other taxes",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    )
    legal_tip = fields.Monetary(
        string="Legal tip amount",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id'
    ) 
    withholding_itbis = fields.Monetary(
        string="Withholding ITBIS",
        compute='_compute_withholding_taxes',
        currency_field='company_currency_id',
    )
    income_withholding = fields.Monetary(
        string="Income Withholding",
        compute='_compute_withholding_taxes',
        currency_field='company_currency_id'
    )
    payment_date = fields.Date(
        string="Payment date",
        compute='_compute_invoice_payment_date', 
        store=True,
    )
    payment_form = fields.Selection(
        string="Payment form",
        selection=[
            ('01', 'Cash'),
            ('02', 'Check / Transfer / Deposit'),
            ('03', 'Credit Card / Debit Card'),
            ('04', 'Credit'), 
            ('05', 'Swap'),
            ('06', 'Credit Note'), 
            ('07', 'Mixed')
        ],
        compute='_compute_in_invoice_payment_form',
    )
    is_exterior = fields.Boolean(
        compute='_compute_is_exterior', 
    )
    service_type = fields.Selection(
        string='Service type',
        selection=[
            ('01', 'Personnel Expenses'),
            ('02', 'Expenses for Work, Supplies and Services'),
            ('03', 'Rentals'),
            ('04', 'Fixed Asset Expenses'),
            ('05', 'Representation Expenses'),
            ('06', 'Financial Expenses'),
            ('07', 'Insurance Expenses'),
            ('08', 'Royalties and Other Intangibles Expenses')
        ]
    )
    service_type_detail = fields.Many2one(
        string='Service type detail',
        comodel_name='invoice.service.type.detail',
    )
    fiscal_status = fields.Selection(
        selection=[
            ('normal', 'Partial'), 
            ('done', 'Reported'), 
            ('blocked', 'Not Sent')
        ],
        copy=False,
        help="* The \'Green\' status means the invoice was sent to the DGII.\n"
        "* The \'Red\' status means the invoice is in a DGII report but has not yet been sent to the DGII.\n"
        "* The \'Grey\' status means Has not yet been reported or was partially reported.",
        default='normal'
    )

    @api.model
    def norma_recompute(self):
        """
        This method add all compute fields into []env
        add_todo and then recompute
        all compute fields in case dgii config change and need to recompute.
        :return:
        """
        active_ids = self._context.get("active_ids")
        invoice_ids = self.browse(active_ids)
        for k, v in self.fields_get().items():
            if v.get("store") and v.get("depends"):
                self.env.add_todo(self._fields[k], invoice_ids)

        self.recompute()
