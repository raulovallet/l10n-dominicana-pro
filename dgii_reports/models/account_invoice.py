import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from collections import defaultdict

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
        'invoice_line_ids.price_subtotal',
        'invoice_line_ids.balance'
    )
    def _compute_amount_fields(self):
        
        """Compute Purchase amount by product type"""
        
        for inv in self:
            service_amount = 0
            good_amount = 0
            
            if inv.state != 'draft' and inv.invoice_date:
                for line in inv.invoice_line_ids:
                    if not line.product_id:
                        service_amount += abs(line.balance)
                    
                    elif line.product_id.type in ['product', 'consu']:
                        good_amount += abs(line.balance)
                    
                    else:
                        service_amount += abs(line.balance)
                
                service_amount = service_amount
                good_amount = good_amount

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
        cash        -- Efectivo code 01
        bank        -- Cheques / Transferencias / Depósitos code 02
        card        -- Tarjeta Crédito / Débito code 03
        credit      -- Compra a Crédito code 04
        swap        -- Permuta code 05
        credit_note -- Notas de Crédito code 06
        mixed       -- Mixto code 07
        """
        payment_code = "mixed"
        payments_widget = self._get_invoice_payment_widget()
        
        if len(payments_widget) > 1:
            return payment_code

        for payment in payments_widget:
            payment_id = self.env['account.payment'].browse(payment.get('account_payment_id', False))
            move_id = self.env['account.move'].browse(payment.get('move_id', False))
            
            if payment_id and payment_id.journal_id.type in ['cash', 'bank']:
                payment_code = payment_id.journal_id.payment_form
            
            # If payment is account move assume it is a credit note
            if move_id.is_invoice():
                payment_code = "credit_note"

        return payment_code

    @api.depends('payment_state')
    def _compute_in_invoice_payment_form(self):
        for inv in self:
            if inv.payment_state in ('paid', 'in_payment'):
                payment_dict = {
                    'cash': '01', 
                    'bank': '02', 
                    'card': '03',
                    'credit': '04', 
                    'swap': '05',
                    'credit_note': '06', 
                    'mixed': '07'
                }
                inv.payment_form = payment_dict.get(inv._get_payment_string())
            else:
                inv.payment_form = '04'

    @api.depends('fiscal_type_id')
    def _compute_is_exterior(self):
        for inv in self:
            inv.is_exterior = True if inv.fiscal_type_id and \
                inv.fiscal_type_id.prefix in ('B17', False) else False

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
        currency_field='company_currency_id',
        store=True
    )
    good_total_amount = fields.Monetary(
        string="Good Total Amount",
        compute='_compute_amount_fields',
        currency_field='company_currency_id',
        store=True
    )
    invoiced_itbis = fields.Monetary(
        string="Invoiced ITBIS",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    proportionality_tax = fields.Monetary(
        string="Proportionality Tax",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    cost_itbis = fields.Monetary(
        string="Cost Itbis",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    advance_itbis = fields.Monetary(
        string="Advanced ITBIS",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    isr_withholding_type = fields.Char(
        string="ISR Withholding Type",
        compute='_compute_isr_withholding_type',
        size=2,
        store=True
    )
    selective_tax = fields.Monetary(
        string="Selective Tax",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    other_taxes = fields.Monetary(
        string="Other taxes",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    )
    legal_tip = fields.Monetary(
        string="Legal tip amount",
        compute='_compute_taxes_fields',
        currency_field='company_currency_id',
        store=True
    ) 
    withholding_itbis = fields.Monetary(
        string="Withholding ITBIS",
        compute='_compute_withholding_taxes',
        currency_field='company_currency_id',
        store=True
    )
    income_withholding = fields.Monetary(
        string="Income Withholding",
        compute='_compute_withholding_taxes',
        currency_field='company_currency_id',
        store=True
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
            ('blocked', 'Not Sent'),
            ('done', 'Reported'), 
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

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.constrains('tax_line_id', 'tax_ids')
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice"""

        for line in self:
            if line.tax_line_id and \
                line.move_id.is_invoice() and \
                line.move_id.is_l10n_do_fiscal_invoice:

                isr_taxes = [
                    tax_line.tax_line_id.isr_retention_type 
                    for tax_line in line.move_id._get_tax_line_ids()
                    if tax_line.tax_line_id.l10n_do_tax_type == 'isr'
                ]
                
                if len(set(isr_taxes)) > 1:
                    raise ValidationError(_('An invoice cannot have multiple withholding taxes.'))
