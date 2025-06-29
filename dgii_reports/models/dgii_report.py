# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2025 Raul Ovalle <raul.ovalle@jenrax.com>

import calendar
import base64
from datetime import datetime as dt, timedelta
import re
import pycountry

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DgiiReport(models.Model):
    _name = 'dgii.reports'
    _description = "DGII Report"
    _inherit = ['mail.thread']

    
    def _compute_previous_report_pending(self):
        for report in self:
            previous = self.search([('company_id', '=', report.company_id.id),
                                    ('state', 'in', ('draft', 'generated')),
                                    ('id', '!=', self.id)],
                                   order='create_date asc',
                                   limit=1)
            if previous:
                previous_date = dt.strptime('01/' + previous.name,
                                            '%d/%m/%Y').date()
                current_date = dt.strptime('01/' + self.name,
                                           '%d/%m/%Y').date()
                report.previous_report_pending = True if previous_date < \
                    current_date else False
            else:
                report.previous_report_pending = False

    name = fields.Char(
        string='Period', 
        required=True, size=7
    )
    state = fields.Selection(
        string="state",
        selection=[
            ('draft', 'New'), 
            ('error', 'With error'),
            ('generated', 'Generated'), 
            ('sent', 'Sent')
        ],
        default='draft',
        copy=False,
        tracking=True    
    )
    previous_balance = fields.Float(
        string='Previous balance', 
        copy=False
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        related='company_id.currency_id',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    previous_report_pending = fields.Boolean(
        compute='_compute_previous_report_pending'
    )
    start_date = fields.Date(
        compute='_compute_dates', 
        string='Start Date',
        store=True
    )
    end_date = fields.Date(
        compute='_compute_dates', 
        string='End Date',
        store=True
    )
    
    @api.depends('name')
    def _compute_dates(self):
        for report in self:
            start_date = False
            end_date = False
            
            if report.name:
                month, year = report.name.split('/')
                last_day = calendar.monthrange(int(year), int(month))[1]
                start_date = '{}-{}-01'.format(year, month)
                end_date = '{}-{}-{}'.format(year, month, last_day)

            report.start_date = start_date
            report.end_date = end_date

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name, company_id)', 
        _("You cannot have more than one report by period."))
    ]


    def _compute_606_fields(self):
        for rec in self:
            data = {
                'purchase_records': 0,
                'service_total_amount': 0,
                'good_total_amount': 0,
                'purchase_invoiced_amount': 0,
                'purchase_invoiced_itbis': 0,
                'purchase_withholded_itbis': 0,
                'cost_itbis': 0,
                'advance_itbis': 0,
                'income_withholding': 0,
                'purchase_selective_tax': 0,
                'purchase_other_taxes': 0,
                'purchase_legal_tip': 0
            }
            purchase_line_ids = self.env['dgii.reports.purchase.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in purchase_line_ids:
                data['purchase_records'] += 1
                data['service_total_amount'] += inv.service_total_amount if inv.invoice_id.move_type not in ['in_refund'] else inv.service_total_amount * -1
                data['good_total_amount'] += inv.good_total_amount if inv.invoice_id.move_type not in ['in_refund'] else inv.service_total_amount * -1
                data['purchase_invoiced_amount'] += inv.invoiced_amount if inv.invoice_id.move_type not in ['in_refund'] else inv.invoiced_amount * -1
                data['purchase_invoiced_itbis'] += inv.invoiced_itbis if inv.invoice_id.move_type not in ['in_refund'] else inv.invoiced_itbis * -1
                data['purchase_withholded_itbis'] += inv.withholded_itbis if inv.invoice_id.move_type not in ['in_refund'] else inv.withholded_itbis * -1
                data['cost_itbis'] += inv.cost_itbis if inv.invoice_id.move_type not in ['in_refund'] else inv.cost_itbis * -1
                data['advance_itbis'] += inv.advance_itbis if inv.invoice_id.move_type not in ['in_refund'] else inv.advance_itbis * -1
                data['income_withholding'] += inv.income_withholding if inv.invoice_id.move_type not in ['in_refund'] else inv.income_withholding * -1
                data['purchase_selective_tax'] += inv.selective_tax if inv.invoice_id.move_type not in ['in_refund'] else inv.selective_tax * -1
                data['purchase_other_taxes'] += inv.other_taxes if inv.invoice_id.move_type not in ['in_refund'] else inv.other_taxes * -1
                data['purchase_legal_tip'] += inv.legal_tip if inv.invoice_id.move_type not in ['in_refund'] else inv.legal_tip * -1

            rec.purchase_records = abs(data['purchase_records'])
            rec.service_total_amount = abs(data['service_total_amount'])
            rec.good_total_amount = abs(data['good_total_amount'])
            rec.purchase_invoiced_amount = abs(data['purchase_invoiced_amount'])
            rec.purchase_invoiced_itbis = abs(data['purchase_invoiced_itbis'])
            rec.purchase_withholded_itbis = abs(data['purchase_withholded_itbis'])
            rec.cost_itbis = abs(data['cost_itbis'])
            rec.advance_itbis = abs(data['advance_itbis'])
            rec.income_withholding = abs(data['income_withholding'])
            rec.purchase_selective_tax = abs(data['purchase_selective_tax'])
            rec.purchase_other_taxes = abs(data['purchase_other_taxes'])
            rec.purchase_legal_tip = abs(data['purchase_legal_tip'])

    
    def _compute_607_fields(self):
        for rec in self:
            data = {
                'sale_records': 0,
                'sale_invoiced_amount': 0,
                'sale_invoiced_itbis': 0,
                'sale_withholded_itbis': 0,
                'sale_withholded_isr': 0,
                'sale_selective_tax': 0,
                'sale_other_taxes': 0,
                'sale_legal_tip': 0
            }
            sale_line_ids = self.env['dgii.reports.sale.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in sale_line_ids:
                data['sale_records'] += 1
                data['sale_invoiced_amount'] += inv.invoiced_amount if inv.invoice_id.move_type not in ['out_refund'] else inv.invoiced_amount * -1
                data['sale_invoiced_itbis'] += inv.invoiced_itbis if inv.invoice_id.move_type not in ['out_refund'] else inv.invoiced_itbis * -1
                data['sale_withholded_itbis'] += inv.third_withheld_itbis if inv.invoice_id.move_type not in ['out_refund'] else inv.third_withheld_itbis * -1
                data['sale_withholded_isr'] += inv.third_income_withholding if inv.invoice_id.move_type not in ['out_refund'] else inv.third_income_withholding * -1
                data['sale_selective_tax'] += inv.selective_tax if inv.invoice_id.move_type not in ['out_refund'] else inv.selective_tax * -1
                data['sale_other_taxes'] += inv.other_taxes if inv.invoice_id.move_type not in ['out_refund'] else inv.other_taxes * -1
                data['sale_legal_tip'] += inv.legal_tip if inv.invoice_id.move_type not in ['out_refund'] else inv.legal_tip * -1

            rec.sale_records = abs(data['sale_records'])
            rec.sale_invoiced_amount = abs(data['sale_invoiced_amount'])
            rec.sale_invoiced_itbis = abs(data['sale_invoiced_itbis'])
            rec.sale_withholded_itbis = abs(data['sale_withholded_itbis'])
            rec.sale_withholded_isr = abs(data['sale_withholded_isr'])
            rec.sale_selective_tax = abs(data['sale_selective_tax'])
            rec.sale_other_taxes = abs(data['sale_other_taxes'])
            rec.sale_legal_tip = abs(data['sale_legal_tip'])

    
    def _compute_608_fields(self):
        for rec in self:
            cancel_line_ids = self.env['dgii.reports.cancel.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            rec.cancel_records = len(cancel_line_ids)

    
    def _compute_609_fields(self):
        for rec in self:
            data = {
                'exterior_records': 0,
                'presumed_income': 0,
                'exterior_withholded_isr': 0,
                'exterior_invoiced_amount': 0
            }
            external_line_ids = self.env['dgii.reports.exterior.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in external_line_ids:
                data['exterior_records'] += 1
                data['presumed_income'] += inv.presumed_income if inv.invoice_id.move_type in ['out_refund', 'in_refund'] else inv.presumed_income * -1
                data['exterior_withholded_isr'] += inv.withholded_isr if inv.invoice_id.move_type in ['out_invoice', 'in_refund'] else inv.withholded_isr * -1
                data['exterior_invoiced_amount'] += inv.invoiced_amount if inv.invoice_id.move_type in ['out_invoice', 'in_refund'] else inv.invoiced_amount * -1

            rec.exterior_records = abs(data['exterior_records'])
            rec.presumed_income = abs(data['presumed_income'])
            rec.exterior_withholded_isr = abs(data['exterior_withholded_isr'])
            rec.exterior_invoiced_amount = abs(
                data['exterior_invoiced_amount'])

    # 606
    purchase_records = fields.Integer(compute='_compute_606_fields')
    service_total_amount = fields.Monetary(compute='_compute_606_fields')
    good_total_amount = fields.Monetary(compute='_compute_606_fields')
    purchase_invoiced_amount = fields.Monetary(compute='_compute_606_fields')
    purchase_invoiced_itbis = fields.Monetary(compute='_compute_606_fields')
    purchase_withholded_itbis = fields.Monetary(compute='_compute_606_fields')
    cost_itbis = fields.Monetary(compute='_compute_606_fields')
    advance_itbis = fields.Monetary(compute='_compute_606_fields')
    income_withholding = fields.Monetary(compute='_compute_606_fields')
    purchase_selective_tax = fields.Monetary(compute='_compute_606_fields')
    purchase_other_taxes = fields.Monetary(compute='_compute_606_fields')
    purchase_legal_tip = fields.Monetary(compute='_compute_606_fields')
    purchase_filename = fields.Char()
    purchase_binary = fields.Binary(string='606 file')

    # 607
    sale_records = fields.Integer(compute='_compute_607_fields')
    sale_invoiced_amount = fields.Float(compute='_compute_607_fields')
    sale_invoiced_itbis = fields.Float(compute='_compute_607_fields')
    sale_withholded_itbis = fields.Float(compute='_compute_607_fields')
    sale_withholded_isr = fields.Float(compute='_compute_607_fields')
    sale_selective_tax = fields.Float(compute='_compute_607_fields')
    sale_other_taxes = fields.Float(compute='_compute_607_fields')
    sale_legal_tip = fields.Float(compute='_compute_607_fields')
    sale_filename = fields.Char()
    sale_binary = fields.Binary(string='607 file')

    # 608
    cancel_records = fields.Integer(compute='_compute_608_fields')
    cancel_filename = fields.Char()
    cancel_binary = fields.Binary(string='608 file')

    # 609
    exterior_records = fields.Integer(compute='_compute_609_fields')
    presumed_income = fields.Float(compute='_compute_609_fields')
    exterior_withholded_isr = fields.Float(compute='_compute_609_fields')
    exterior_invoiced_amount = fields.Float(compute='_compute_609_fields')
    exterior_filename = fields.Char()
    exterior_binary = fields.Binary(string='609 file')

    # IT-1
    it1_section_1_line_ids = fields.One2many(
        string='IT1 section 1 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '1')]
    )
    it1_section_2_line_ids = fields.One2many(
        string='IT1 section 2 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '2')]
    )
    it1_section_3_line_ids = fields.One2many(
        string='IT1 section 3 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '3')]
    )
    it1_section_4_line_ids = fields.One2many(
        string='IT1 section 4 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '4')]
    )
    it1_section_5_line_ids = fields.One2many(
        string='IT1 section 5 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '5')]
    )
    it1_section_6_line_ids = fields.One2many(
        string='IT1  section 6 lines',
        comodel_name='dgii.reports.it1.line',
        inverse_name='dgii_report_id',
        domain=[('section', '=', '6')]
    )

    # General Summary of Consumer Invoices
    csmr_ncf_qty = fields.Integer(
        string='Issued Consumer NCF Qty', 
        copy=False
    )
    csmr_ncf_total_amount = fields.Monetary(
        string='Invoiced Amount Total',
        copy=False
    )
    csmr_ncf_total_itbis = fields.Monetary(
        string='Invoiced ITBIS Total', 
        copy=False,
    )
    csmr_ncf_total_isc = fields.Monetary(
        string='Selective Tax', 
        copy=False
    )
    csmr_ncf_total_other = fields.Monetary(
        string='Other Taxes Total', 
        copy=False
    )
    csmr_ncf_total_lgl_tip = fields.Monetary(
        string='Legal Tip Total', 
        copy=False
    )

    # General Summary of Consumer Invoices - Sale Form
    csmr_cash = fields.Monetary(
        string='Consumer Cash', 
        copy=False
    )
    csmr_bank = fields.Monetary(
        string='Consumer Check / Transfer / Deposit',
        copy=False
    )
    csmr_card = fields.Monetary(
        string='Consumer Credit Card / Debit Card',
        copy=False
    )
    csmr_credit = fields.Monetary(
        string='Consumer Credit', 
        copy=False
    )
    csmr_bond = fields.Monetary(
        string='Consumer Gift certificates or vouchers', 
        copy=False
    )
    csmr_swap = fields.Monetary(
        string='Consumer Swap', 
        copy=False
    )
    csmr_others = fields.Monetary(
        string='ConsumerOther Sale Forms', 
        copy=False
    )

    def _get_csmr_vals_dict(self):
        return {
            'csmr_ncf_qty': 0,
            'csmr_ncf_total_amount': 0,
            'csmr_ncf_total_itbis': 0,
            'csmr_ncf_total_isc': 0,
            'csmr_ncf_total_other': 0,
            'csmr_ncf_total_lgl_tip': 0,
            'csmr_cash': 0,
            'csmr_bank': 0,
            'csmr_card': 0,
            'csmr_credit': 0,
            'csmr_bond': 0,
            'csmr_swap': 0,
            'csmr_others': 0
        }
    
    def _set_csmr_fields_vals(self, csmr_dict):
        self.write(csmr_dict)

    def _get_country_number(self, partner_id):
        """
        Returns ISO 3166 country number from partner
        country code
        """
        res = False
        if not partner_id.country_id:
            return False
        try:
            country = pycountry.countries.get(
                alpha_2=partner_id.country_id.code)
            res = country.numeric
        except AttributeError:
            return res
        return res

    def _validate_date_format(self, date):
        """Validate date format <MM/YYYY>"""
        if date is not None:
            error = _('Error. Date format must be MM/YYYY')
            if len(date) == 7:
                try:
                    dt.strptime(date, '%m/%Y')
                except ValueError:
                    raise ValidationError(error)
            else:
                raise ValidationError(error)

    @api.model_create_multi
    def create(self, vals_list):
        
        for vals in vals_list:
            self._validate_date_format(vals.get('name'))

        return super(DgiiReport, self).create(vals_list)

    
    def write(self, vals):
        self._validate_date_format(vals.get('name'))
        return super(DgiiReport, self).write(vals)

    def _get_pending_invoices(self, types, states):
        invoice_ids = self.env['account.move'].search([
            '&',
            '|',
            ('withholding_itbis', '!=', 0.0),
            ('income_withholding', '!=', 0.0),
            ('fiscal_status', '=', 'normal'),
            ('payment_state', 'in', ('paid', 'in_payment')),
            ('invoice_date', '<', self.start_date),
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', types),
            ('state', 'in', states),
            ('is_l10n_do_fiscal_invoice', '=', True),
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date)
        ])

        return invoice_ids

    def _get_invoices(self, states, types):
        """
        Given rec and state, return a recordset of invoices
        :param state: a list of invoice state
        :param type: a list of invoice type
        :return: filtered invoices
        """

        invoice_ids = self.env['account.move'].search([
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date),
            ('company_id', '=', self.company_id.id),
            ('is_l10n_do_fiscal_invoice', '=', True),
            ('state', 'in', states),
            ('move_type', 'in', types),
            ('fiscal_type_id.prefix', '!=', False),
        ], order='invoice_date asc')
        
        # Append pending invoices (fiscal_status = Partial, state = Paid)
        invoice_ids |= self._get_pending_invoices(types, states)

        return invoice_ids

    def formatted_rnc_cedula(self, vat):
        if vat:
            if len(vat) in [9, 11]:
                id_type = 1 if len(vat) == 9 else 2
                return (vat.strip().replace('-', ''),
                        id_type) if not vat.isspace() else False
            else:
                return False
        else:
            return False

    def _get_formatted_date(self, date):

        return dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d') \
            if isinstance(date, str) else date.strftime('%Y%m%d') \
            if date else ""

    def _get_formatted_amount(self, amount):

        return str('{:.2f}'.format(abs(amount))).ljust(12)

    def process_606_report_data(self, values):

        RNC = str(values['rnc_cedula'] if values['rnc_cedula'] else "").strip()
        ID_TYPE = str(values['identification_type'] if values['identification_type'] else "").strip()
        EXP_TYPE = str(
            values['expense_type'] if values['expense_type'] else "").strip()
        NCF = str(values['fiscal_invoice_number']).strip()
        NCM = str(values['modified_invoice_number'] if values['modified_invoice_number'] else "").strip()
        INV_DATE = str(self._get_formatted_date( values['invoice_date'])).strip()
        PAY_DATE = str(self._get_formatted_date(values['payment_date'])).strip()
        SERV_AMOUNT = self._get_formatted_amount(values['service_total_amount']).strip()
        GOOD_AMOUNT = self._get_formatted_amount(values['good_total_amount']).strip()
        INV_AMOUNT = self._get_formatted_amount(values['invoiced_amount']).strip()
        INV_ITBIS = self._get_formatted_amount(values['invoiced_itbis']).strip()
        WH_ITBIS = self._get_formatted_amount(values['withholded_itbis']).strip()
        PROP_ITBIS = self._get_formatted_amount(values['proportionality_tax']).strip()
        COST_ITBIS = self._get_formatted_amount(values['cost_itbis']).strip()
        ADV_ITBIS = self._get_formatted_amount(values['advance_itbis']).strip()
        PP_ITBIS = ''
        WH_TYPE = str(values['isr_withholding_type'] if values['isr_withholding_type'] else "").strip()
        INC_WH = self._get_formatted_amount(values['income_withholding']).strip()
        PP_ISR = ''
        ISC = self._get_formatted_amount(values['selective_tax']).strip()
        OTHR = self._get_formatted_amount(values['other_taxes']).strip()
        LEG_TIP = self._get_formatted_amount(values['legal_tip']).strip()
        PAY_FORM = str(
            values['payment_type'] if values['payment_type'] else "").strip()

        return "|".join([
            RNC, ID_TYPE, EXP_TYPE, NCF, NCM, INV_DATE, PAY_DATE, SERV_AMOUNT,
            GOOD_AMOUNT, INV_AMOUNT, INV_ITBIS, WH_ITBIS, PROP_ITBIS,
            COST_ITBIS, ADV_ITBIS, PP_ITBIS, WH_TYPE, INC_WH, PP_ISR, ISC,
            OTHR, LEG_TIP, PAY_FORM
        ])

    def _generate_606_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''), '%m%Y').strftime('%Y%m')

        header = "606|{}|{}|{}".format(
            str(company_vat), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_606_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_606:
            txt_606.write(str(data))

        self.write({
            'purchase_filename': file_path.replace('/tmp/', ''),
            'purchase_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    
    def _compute_606_data(self):
        for rec in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            PurchaseLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(
                ['posted'], 
                ['in_invoice', 'in_refund']
            )

            line = 0
            report_data = ''
            invoice_ids.filtered(lambda inv: not inv.fiscal_status).write({
                'fiscal_status': 'blocked'
            })
            dgii_report_purchase_line = [] 
            for inv in invoice_ids:
                line += 1
                rnc_ced = self.formatted_rnc_cedula(
                    inv.partner_id.vat
                ) if inv.fiscal_type_id.prefix != 'B17' else \
                    self.formatted_rnc_cedula(
                    inv.company_id.vat)
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'expense_type': inv.expense_type
                    if inv.expense_type else False,
                    'fiscal_invoice_number': inv.ref,
                    'modified_invoice_number': inv.origin_out if
                    inv.move_type == 'in_refund' else False,
                    'invoice_date': inv.invoice_date,
                    'payment_date': inv.payment_date  if self.is_applicable_payment_date(inv) else False,
                    'service_total_amount': inv.service_total_amount,
                    'good_total_amount': inv.good_total_amount,
                    'invoiced_amount': abs(inv.amount_untaxed_signed),
                    'invoiced_itbis': inv.invoiced_itbis,
                    'proportionality_tax': inv.proportionality_tax,
                    'cost_itbis': inv.cost_itbis,
                    'advance_itbis': inv.advance_itbis,
                    'purchase_perceived_itbis': 0,  # Falta computar en la fact
                    'purchase_perceived_isr': 0,  # Falta computarlo en la fact
                    'isr_withholding_type': inv.isr_withholding_type,
                    'withholded_itbis': inv.withholding_itbis if self.is_applicable_for_withholding(inv) else 0,
                    'income_withholding': inv.income_withholding if self.is_applicable_for_withholding(inv) else 0,
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'payment_type': inv.payment_form,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.move_type == 'in_refund' else False
                }
                dgii_report_purchase_line.append(values)
                report_data += self.process_606_report_data(values) + '\n'
                
            PurchaseLine.create(dgii_report_purchase_line)
            self._generate_606_txt(report_data, line)

    def _get_payments_dict(self):
        return {
            'cash': 0,
            'bank': 0,
            'card': 0,
            'credit': 0,
            'swap': 0,
            'bond': 0,
            'others': 0
        }
    
    def _get_sale_payments_forms(self, invoice_id, payments):
        payments_dict = self._get_payments_dict()

        if invoice_id.move_type == 'out_invoice':
            for payment in payments:
                if self.start_date <= payment['payment_date'] <= self.end_date:
                    if payment['payment_form'] not in payments_dict:
                        payments_dict['others'] += payment['amount_company']
                    else:
                        payments_dict[payment['payment_form']] += payment['amount_company']
                else:
                    payments_dict['credit'] += payment['amount_company']
                    
            payments_dict['credit'] += abs(invoice_id.amount_residual_signed)

        return payments_dict

    def _get_income_type_dict(self):
        return {'01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0}

    def _process_income_dict(self, args, invoice):
        income_dict = args
        if invoice.income_type:
            income_dict[invoice.income_type] += abs(invoice.amount_untaxed_signed)
        return income_dict

    def process_607_report_data(self, values):

        RNC = str(values['rnc_cedula'] if values['rnc_cedula'] else "").strip()
        ID_TYPE = str(values['identification_type'] if values['identification_type'] else "").strip()
        NCF = str(values['fiscal_invoice_number']).strip()
        NCM = str(values['modified_invoice_number'] if values['modified_invoice_number'] else "").strip()
        INCOME_TYPE = str(values['income_type']).strip()
        INV_DATE = str(self._get_formatted_date(values['invoice_date'])).strip()
        WH_DATE = str(self._get_formatted_date(values['withholding_date'])).strip()
        INV_AMOUNT = self._get_formatted_amount(values['invoiced_amount']).strip()
        INV_ITBIS = self._get_formatted_amount(values['invoiced_itbis']).strip()
        WH_ITBIS = self._get_formatted_amount(values['third_withheld_itbis']).strip()
        PRC_ITBIS = ''
        WH_ISR = self._get_formatted_amount(values['third_income_withholding']).strip()
        PCR_ISR = ''
        ISC = self._get_formatted_amount(values['selective_tax']).strip()
        OTH_TAX = self._get_formatted_amount(values['other_taxes']).strip()
        LEG_TIP = self._get_formatted_amount(values['legal_tip']).strip()
        CASH = self._get_formatted_amount(values['cash']).strip()
        BANK = self._get_formatted_amount(values['bank']).strip()
        CARD = self._get_formatted_amount(values['card']).strip()
        CRED = self._get_formatted_amount(values['credit']).strip()
        SWAP = self._get_formatted_amount(values['swap']).strip()
        BOND = self._get_formatted_amount(values['bond']).strip()
        OTHR = self._get_formatted_amount(values['others']).strip()

        return "|".join([
            RNC, ID_TYPE, NCF, NCM, INCOME_TYPE, INV_DATE, WH_DATE, INV_AMOUNT,
            INV_ITBIS, WH_ITBIS, PRC_ITBIS, WH_ISR, PCR_ISR, ISC, OTH_TAX,
            LEG_TIP, CASH, BANK, CARD, CRED, SWAP, BOND, OTHR
        ])

    def _generate_607_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = \
            dt.strptime(self.name.replace('/', ''), '%m%Y').strftime('%Y%m')

        header = "607|{}|{}|{}".format(
            str(company_vat), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_607_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_607:
            txt_607.write(str(data))

        self.write({
            'sale_filename': file_path.replace('/tmp/', ''),
            'sale_binary': base64.b64encode(open(file_path, 'rb').read())
        })
        
    def quick_payments_for_invoices(self, invoice_ids):
        """
        Args:
            env          – an Odoo environment (self.env)
            invoice_ids  – iterable of account.move IDs (invoices)

        Returns:
            {invoice_id: [ {payment_form, amount_company, payment_date}, … ] }
        """
        invoice_ids = list(map(int, invoice_ids))           # cast to ints, use list so psycopg2 builds an ARRAY

        self.env.cr.execute("""
            SELECT
                inv.move_id                     AS invoice_id,
                j.payment_form                  AS payment_form,
                pr.amount                       AS amount_company,
                pay_mv.date                     AS payment_date
            FROM   account_move_line inv
            JOIN   account_partial_reconcile pr ON inv.id IN (pr.debit_move_id, pr.credit_move_id)
            JOIN   account_move_line pay_ml     ON pay_ml.id = CASE
                                                                WHEN inv.id = pr.debit_move_id
                                                                THEN pr.credit_move_id
                                                                ELSE pr.debit_move_id
                                                             END
            JOIN   account_move pay_mv          ON pay_mv.id = pay_ml.move_id
            JOIN   account_journal j            ON j.id = pay_mv.journal_id
            WHERE  inv.move_id = ANY(%s::int[]);
        """, [invoice_ids])

        from collections import defaultdict
        result = defaultdict(list)
        for inv_id, form, amt, date in self.env.cr.fetchall():
            result[inv_id].append({
                "payment_form":   form,   # journal.payment_form
                "amount_company": amt,    # company-currency amount
                "payment_date":   date,   # payment move date
            })
        return result
    
    def _compute_607_data(self):
        for rec in self:
            SaleLine = self.env['dgii.reports.sale.line']
            SaleLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(
                ['posted'], 
                ['out_invoice', 'out_refund']
            )

            line = 0
            excluded_line = line
            payment_dict = self._get_payments_dict()
            income_dict = self._get_income_type_dict()
            csmr_dict = self._get_csmr_vals_dict()
            dgii_report_sale_line = []

            report_data = ''
            invoice_ids.filtered(lambda inv: not inv.fiscal_status and inv.ref).write({
                'fiscal_status': 'blocked'
            }) 
            payments_map = self.quick_payments_for_invoices(invoice_ids.ids)
            for inv in invoice_ids:
                income_dict = self._process_income_dict(income_dict, inv)
                rnc_ced = self.formatted_rnc_cedula(
                    inv.partner_id.vat
                ) if inv.fiscal_type_id.prefix != 'B12' \
                    else self.formatted_rnc_cedula(inv.company_id.vat)
                inv_payments_list = payments_map.get(inv.id, [])
                payments = self._get_sale_payments_forms(inv, inv_payments_list)
                inv_sign = -1 if inv.move_type == 'out_refund' else 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'fiscal_invoice_number': inv.ref,
                    'modified_invoice_number':
                        inv.origin_out if inv.origin_out and
                        inv.origin_out[-10:-8] in ['01', '02', '14', '15'] else
                        False,
                    'income_type': inv.income_type,
                    'invoice_date': inv.invoice_date,
                    'withholding_date': inv.payment_date if inv.move_type != 'out_refund' and self.is_applicable_for_withholding(inv) else False,
                    'invoiced_amount': abs(inv.amount_untaxed_signed),
                    'invoiced_itbis': inv.invoiced_itbis,
                    'third_withheld_itbis': inv.withholding_itbis if self.is_applicable_for_withholding(inv) else 0,
                    'third_income_withholding': inv.income_withholding if self.is_applicable_for_withholding(inv) else 0,
                    'perceived_itbis': 0,  # Pendiente
                    'perceived_isr': 0,  # Pendiente
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.move_type == 'out_refund' else False,
                    'cash': payments.get('cash', 0) * inv_sign,
                    'bank': payments.get('bank', 0) * inv_sign,
                    'card': payments.get('card', 0) * inv_sign,
                    'credit': payments.get('credit', 0) * inv_sign,
                    'swap': payments.get('swap', 0) * inv_sign,
                    'bond': payments.get('bond', 0) * inv_sign,
                    'others': payments.get('others', 0) * inv_sign
                }

                if str(values['fiscal_invoice_number'])[-10:-8] == '02':
                    csmr_dict['csmr_ncf_qty'] += 1
                    csmr_dict['csmr_ncf_total_amount'] += \
                        values['invoiced_amount']
                    csmr_dict['csmr_ncf_total_itbis'] += \
                        values['invoiced_itbis']
                    csmr_dict['csmr_ncf_total_isc'] += values['selective_tax']
                    csmr_dict['csmr_ncf_total_other'] += values['other_taxes']
                    csmr_dict['csmr_ncf_total_lgl_tip'] += values['legal_tip']
                    csmr_dict['csmr_cash'] += values['cash']
                    csmr_dict['csmr_bank'] += values['bank']
                    csmr_dict['csmr_card'] += values['card']
                    csmr_dict['csmr_credit'] += values['credit']
                    csmr_dict['csmr_bond'] += values['bond']
                    csmr_dict['csmr_swap'] += values['swap']
                    csmr_dict['csmr_others'] += values['others']

                line += 1
                values.update({'line': line})
                dgii_report_sale_line.append(values)
                if str(values.get('fiscal_invoice_number'))[-10:-8] == \
                        '02' and abs(inv.amount_untaxed_signed) < 250000:
                    excluded_line += 1
                    # Excluye las facturas de Consumo
                    # con monto menor a 250000 solo del txt
                    pass
                else:
                    report_data += self.process_607_report_data(values) + '\n'

                for k in payment_dict:
                    payment_dict[k] += payments[k] * -1 if inv.move_type == \
                        'out_refund' else payments[k]
                        
            SaleLine.create(dgii_report_sale_line)
            self._set_csmr_fields_vals(csmr_dict)
            self._generate_607_txt(report_data, line - excluded_line)

    def process_608_report_data(self, values):

        NCF = str(values['fiscal_invoice_number']).ljust(11)
        INV_DATE = str(self._get_formatted_date(
            values['invoice_date'])).ljust(8)
        ANU_TYPE = str(values['annulation_type']).ljust(2)

        return "|".join([NCF, INV_DATE, ANU_TYPE])

    def _generate_608_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''), '%m%Y').strftime('%Y%m')

        header = "608|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_608_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_608:
            txt_608.write(str(data))

        self.write({
            'cancel_filename': file_path.replace('/tmp/', ''),
            'cancel_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    
    def _compute_608_data(self):
        for rec in self:
            CancelLine = self.env['dgii.reports.cancel.line']
            CancelLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(
                ['cancel'], 
                ['out_invoice', 'out_refund'],
            )
            line = 0
            report_data = ''
            invoice_ids.filtered(lambda inv: not inv.fiscal_status and inv.ref).write({
                'fiscal_status': 'blocked'
            })
            dgii_report_cancel_line = []
            for inv in invoice_ids:
                if inv.ref:
                    line += 1
                    values = {
                        'dgii_report_id': rec.id,
                        'line': line,
                        'invoice_partner_id': inv.partner_id.id,
                        'fiscal_invoice_number': inv.ref,
                        'invoice_date': inv.invoice_date,
                        'annulation_type': inv.annulation_type,
                        'invoice_id': inv.id
                    }
                    dgii_report_cancel_line.append(values)
                    report_data += self.process_608_report_data(values) + '\n'
                    
            CancelLine.create(dgii_report_cancel_line)
            self._generate_608_txt(report_data, line)

    def process_609_report_data(self, values):

        LEGAL_NAME = str(values['legal_name']).ljust(50)
        ID_TYPE = str(values['tax_id_type'] if values['tax_id_type'] else "")
        TAX_ID = str(values['tax_id'] if values['tax_id'] else "").ljust(50)
        CNT_CODE = str(
            values['country_code'] if values['country_code'] else "").ljust(3)
        PST = str(values['purchased_service_type']
                  if values['purchased_service_type'] else "").ljust(2)
        STD = str(values['service_type_detail']
                  if values['service_type_detail'] else "").ljust(2)
        REL_PART = str(
            values['related_part'] if values['related_part'] else "0").ljust(1)
        DOC_NUM = str(
            values['doc_number'] if values['doc_number'] else "").ljust(30)
        DOC_DATE = str(self._get_formatted_date(values['doc_date'])).ljust(8)
        INV_AMOUNT = self._get_formatted_amount(values['invoiced_amount'])
        ISR_DATE = str(self._get_formatted_date(
            values['isr_withholding_date'])).ljust(8)
        PRM_INCM = self._get_formatted_amount(values['presumed_income'])
        WH_ISR = self._get_formatted_amount(values['withholded_isr'])

        return "|".join([
            LEGAL_NAME, ID_TYPE, TAX_ID, CNT_CODE, PST, STD, REL_PART, DOC_NUM,
            DOC_DATE, INV_AMOUNT, ISR_DATE, PRM_INCM, WH_ISR
        ])

    def _generate_609_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''),
                             '%m%Y').strftime('%Y%m')

        header = "609|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_609_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_609:
            txt_609.write(str(data))

        self.write({
            'exterior_filename': file_path.replace('/tmp/', ''),
            'exterior_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    
    def _compute_609_data(self):
        for rec in self:
            ExteriorLine = self.env['dgii.reports.exterior.line']
            ExteriorLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(
                ['posted'], 
                ['in_invoice', 'in_refund']
            ).filtered(lambda inv: (inv.partner_id.country_id.code != 'DO') and \
                                    (inv.fiscal_type_id.prefix == 'B17'))
            line = 0
            report_data = ''
            invoice_ids.filtered(lambda inv: not inv.fiscal_status).write({
                'fiscal_status': 'blocked'
            }) 
            dgii_report_exterior_line = []
            for inv in invoice_ids:
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'legal_name': inv.partner_id.name,
                    'tax_id_type': 1 if inv.partner_id.company_type == 'individual' else 2,
                    'tax_id': inv.partner_id.vat,
                    'country_code': self._get_country_number(inv.partner_id),
                    'purchased_service_type': int(inv.service_type),
                    'service_type_detail': inv.service_type_detail.code,
                    'related_part': int(inv.partner_id.related),
                    'doc_number': inv.name,
                    'doc_date': inv.invoice_date,
                    'invoiced_amount': inv.amount_untaxed,
                    'isr_withholding_date': inv.payment_date if self.is_applicable_for_withholding(inv) else False,
                    'presumed_income': 0,  # Pendiente
                    'withholded_isr': inv.income_withholding if self.is_applicable_for_withholding(inv) else 0,
                    'invoice_id': inv.id
                }
                dgii_report_exterior_line.append(values)
                report_data += self.process_609_report_data(values) + '\n'

            ExteriorLine.create(dgii_report_exterior_line)
            self._generate_609_txt(report_data, line)
    
    def _get_section_attachment_a_report(self, key):
        if key in list(range(1, 12)):
            return '1'
        elif key in list(range(12, 34)):
            return '2'
        elif key in list(range(34, 43)):
            return '3'
        elif key in list(range(43, 45)):
            return '4'
        elif key in list(range(45, 57)):
            return '5'
        else:
            return False

    def _get_attachment_a_dictionary(self):
        report_lines = {}
        names = {
            1: _('VALID PROOFS FOR TAX CREDIT (01 and 31)'),
            2: _('CONSUMPTION PROOFS (02 and 32)'),
            3: _('PROOFS DEBIT NOTE (03 and 33)'),
            4: _('PROOFS OF CREDIT NOTE (04 and 34)'),
            5: _('SINGLE INCOME REGISTRY PROOFS (12)'),
            6: _('SPECIAL REGIME REGISTRATION PROOFS (14 and 44)'),
            7: _('GOVERNMENT PROOFS (15 and 45)'),
            8: _('PROOFS FOR EXPORTS (16 and 46)'),
            9: _('OTHER OPERATIONS (POSITIVE)'),
            10: _('OTHER OPERATIONS (NEGATIVE)'),
            11: _('TOTAL OPERATIONS (Sum boxes 1+2+3-4+5+6+7+8+9-10)'),
            12: _('CASH'),
            13: _('CHECK / TRANSFER'),
            14: _('DEBIT / CREDIT CARD'),
            15: _('ON CREDIT'),
            16: _('BONUSES OR GIFT CERTIFICATE'),
            17: _('SWAPS'),
            18: _('OTHER FORMS OF SALE'),
            19: _('TOTAL OPERATIONS BY TYPE OF SALE (Sum boxes 12+13+14+15+16+17+18)'),
            20: _('INCOME FROM OPERATIONS (NON-FINANCIAL)'),
            21: _('FINANCIAL INCOME'),
            22: _('EXTRAORDINARY INCOME'),
            23: _('INCOME FROM LEASE'),
            24: _('INCOME FROM THE SALES OF DEPRECIABLE ASSETS'),
            25: _('OTHER INCOME'),
            26: _('TOTAL BY TYPE OF INCOME (Sum boxes 20+21+22+23+24+25)'),
            27: _('COMPUTABLE PAYMENTS FOR WITHHOLDINGS (Norm No. 08-04)'),
            28: _('COMPUTABLE PAYMENTS FOR SALES OF AIR TRANSPORTATION TICKETS (Norm No. 02-05) (BSP-IATA)'),
            29: _('COMPUTABLE PAYMENTS FOR OTHER WITHHOLDINGS (Norm No. 02-05)'),
            30: _('COMPUTABLE PAYMENTS FOR SALES OF ACCOMMODATION AND OCCUPANCY PACKAGES'),
            31: _('CREDIT FOR WITHHOLDING BY STATE ENTITIES'),
            32: _('COMPUTABLE PAYMENTS FOR ITBIS PERCEIVED'),
            33: _('TOTAL COMPUTABLE PAYMENTS FOR WITHHOLDINGS/PERCEPTION (Sum boxes 27+28+29+30+31+32)'),
            34: _('TECHNICAL MANAGEMENT (Art. 4 Norma 07-07)'),
            35: _('ADMINISTRATION AGREEMENT (Art. 4 Paragraph I, Norm 07-07)'),
            36: _('CONSULTING / FEES'),
            37: _('TOTAL CONSTRUCTION OPERATIONS (Total Invoiced: Sum boxes 34+35, Amount: Sum boxes 34+35+36)'),
            38: _('OPERATIONS NOT SUBJECT TO ITBIS FOR CONSTRUCTION SERVICES '
                  '(Subtract Box 37 Total Invoiced - Amount Subject to ITBIS)'),
            39: _('SALES OF GOODS BY COMMISSION'),
            40: _('SALES OF SERVICES ON BEHALF OF THIRD PARTIES'),
            41: _('TOTAL COMMISSION OPERATIONS (Sum boxes 39+40)'),
            42: _('OPERATIONS NOT SUBJECT TO ITBIS FOR COMMISSIONS '
                  '(Subtract Box 41 Total Invoiced - Amount Subject to ITBIS)'),
            43: _('TOTAL CREDIT NOTES ISSUED WITH MORE THAN THIRTY'),
            44: _('TOTAL INVOICES IN TAX RECEIPTS FOR SPECIAL REGIMES'),
            45: _('IN OPERATIONS OF PRODUCERS OF EXEMPT GOODS OR SERVICES'),
            46: _('TO BE INCLUDED IN ASSETS (CATEGORY I)'),
            47: _('OTHER NON-DEDUCTIBLE ITBIS PAID'),
            48: _('TOTAL NON-DEDUCTIBLE ITBIS (45+46+47)'),
            49: _('IN THE PRODUCTION AND/OR SALE OF EXPORTED GOODS'),
            50: _('IN THE PRODUCTION AND/OR SALE OF TAXED ASSETS'),
            51: _('IN THE PROVISION OF TAXED SERVICES'),
            52: _('TOTAL ITBIS DEDUCTIBLE NOT SUBJECT TO PROPORTIONALITY (49+50+51)'),
            53: _('ITBIS SUBJECT TO PROPORTIONALITY'),
            54: _('COEFFICIENT OF PROPORTIONALITY ((((Boxes 2 + 5 + 10 of IT1) / Box 1 of IT1)) * 100) If applicable.'),
            55: _('ITBIS ADMITTED BY APPLICATION OF PROPORTIONALITY (box 53 * 54)'),
            56: _('TOTAL ITBIS DEDUCTIBLE (52+55)')
        }

        for key, value in names.items():
            report_lines.update({
                key: {
                    'name': value,
                    'sequence': key,
                    'dgii_report_id': self.id,
                    'section': self._get_section_attachment_a_report(key),
                    'coefficient': 0,
                    'quantity': 0,
                    'local_purchase': 0,
                    'services': 0,
                    'imports': 0,
                    'amount': 0,
                    'invoice_ids': [(6, 0, [])],
                }
            })

        # Titles
        report_lines.update({
            'AII': {
                'name': _('II. OPERATIONS REPORTED IN THE 607, SALES BOOK AND ELECTRONIC INVOICE (E-NCF) BY TYPE OF NCF'),
                'display_type': 'line_section',
                'sequence': 0,
                'dgii_report_id': self.id,
                'section': '1'
            },
            'AIII': {
                'name': _('III. OPERATIONS REPORTED IN THE 607/SALES BOOK AND ELECTRONIC INVOICE (E-NCF) BY TYPE OF '
                          'SALE (TOTAL AMOUNT INCLUDING TAXES)'),
                'display_type': 'line_section',
                'sequence': 12,
                'dgii_report_id': self.id,
                'section': '2'
            },
            'AIV': {
                'name': _('IV. OPERATIONS REPORTED IN THE 607/SALES BOOK AND ELECTRONIC INVOICE (E-NCF) BY TYPE OF '
                          'INCOME'),
                'display_type': 'line_section',
                'sequence': 20,
                'dgii_report_id': self.id,
                'section': '2'
            },
            'AV': {
                'name': _('V. COMPUTABLE PAYMENTS FOR WITHHOLDINGS/PERCEPTIONS'),
                'display_type': 'line_section',
                'sequence': 27,
                'dgii_report_id': self.id,
                'section': '2'
            },
            'AVI': {
                'name': _('VI. CONSTRUCTION OPERATIONS'),
                'display_type': 'line_section',
                'sequence': 34,
                'dgii_report_id': self.id,
                'section': '3'
            },
            'AVII': {
                'name': _('VII. COMMISSION OPERATIONS'),
                'display_type': 'line_section',
                'sequence': 39,
                'dgii_report_id': self.id,
                'section': '3'
            },
            'AVIII': {
                'name': _('VIII. INFORMATIVE DATA'),
                'display_type': 'line_section',
                'sequence': 43,
                'dgii_report_id': self.id,
                'section': '4'
            },
            'AIX': {
                'name': _('IX. ITBIS PAID'),
                'display_type': 'line_section',
                'sequence': 45,
                'dgii_report_id': self.id,
                'section': '5'
            },
            'AIXa': {
                'name': _('A) NON-DEDUCTIBLE (Carried to Cost/Expense)'),
                'display_type': 'line_section',
                'sequence': 45,
                'dgii_report_id': self.id,
                'section': '5'
            },
            'AIXb': {
                'name': _('B) DEDUCTIBLE'),
                'display_type': 'line_section',
                'sequence': 49,
                'dgii_report_id': self.id,
                'section': '5'
            },
            'AIXc': {
                'name': _('C) ITBIS SUBJECT TO PROPORTIONALITY (Art. 349 of the Tax Code)'),
                'display_type': 'line_section',
                'sequence': 53,
                'dgii_report_id': self.id,
                'section': '5'
            }
        })

        return report_lines

    def _get_it1_dictionary(self):
        report_lines = {}
        names = {
            1: _('TOTAL OPERATIONS FOR THE PERIOD (From box 11 of Annex A)'),
            2: _('INCOME FROM EXPORTS OF GOODS (Article 342 CT)'),
            3: _('INCOME FROM EXPORTS OF SERVICES (Article 344 CT and Article 14, Paragraph j), Regulation 293-11)'),
            4: _('INCOME FROM LOCAL SALES OF EXEMPT GOODS OR SERVICES (Article 343 and Article 344 CT)'),
            5: _('INCOME FROM THE SALES OF EXEMPT GOODS OR SERVICES BY DESTINATION'),
            6: _('NOT SUBJECT TO ITBIS FOR CONSTRUCTION SERVICES (From box 38 of Annex A)'),
            7: _('NOT SUBJECT TO ITBIS FOR COMMISSIONS (From box 42 of Annex A)'),
            8: _('INCOME FROM LOCAL SALES OF EXEMPT GOODS (Paragraphs III and IV, Article 343 CT)'),
            9: _('TOTAL INCOME FROM NON-TAXED OPERATIONS (Sum of boxes 2+3+4+5+6+7+8)'),
            10: _('TOTAL INCOME FROM TAXED OPERATIONS (Subtract boxes 9 from 1)'),
            11: _('OPERATIONS TAXED AT 18%'),
            12: _('OPERATIONS TAXED AT 16%'),
            13: _('OPERATIONS TAXED AT 9% (Law No. 690-16)'),
            14: _('OPERATIONS TAXED AT 8% (Law No. 690-16)'),
            15: _('OPERATIONS TAXED BY SALES OF DEPRECIABLE ASSETS (Categories 2 and 3)'),
            16: _('ITBIS COLLECTED (18% of box 11)'),
            17: _('ITBIS COLLECTED (16% of box 12)'),
            18: _('ITBIS COLLECTED (9% of box 13) (Law No. 690-16)'),
            19: _('ITBIS COLLECTED (8% of box 14) (Law No. 690-16)'),
            20: _('ITBIS CHARGED FOR SALES OF DEPRECIABLE ASSETS (Categories 2 and 3)'),
            21: _('TOTAL ITBIS COLLECTED (Sum of boxes 16+17+18+19+20)'),
            22: _('ITBIS PAID ON LOCAL PURCHASES'),
            23: _('ITBIS PAID FOR DEDUCTIBLE SERVICES'),
            24: _('ITBIS PAID ON IMPORTS'),
            25: _('TOTAL DEDUCTIBLE ITBIS (Sum of boxes 22+23+24)'),
            26: _('TAX TO PAY (Subtract box 25 from box 21)'),
            27: _('BALANCE IN FAVOR (If box 26 is negative)'),
            28: _('AUTHORIZED COMPENSABLE BALANCES (Other Taxes) AND/OR REFUNDS'),
            29: _('BALANCE IN PREVIOUS FAVOR'),
            30: _('TOTAL COMPUTABLE PAYMENTS FOR WITHHOLDINGS (From box 33 of Annex A)'),
            31: _('OTHER COMPUTABLE PAYMENTS ON ACCOUNT'),
            32: _('AUTHORIZED COMPENSATIONS AND/OR REFUNDS'),
            33: _('DIFFERENCE TO PAY (If the value of boxes 26-28-29-30-31-32 is Positive)'),
            34: _('NEW BALANCE IN FAVOR '
                  '(If the value of boxes (26-28-29-30-31-32 is Negative) or (27+28+29+30+31+32))'),
            35: _('SURCHARGES'),
            36: _('COMPENSATION INTEREST'),
            37: _('SANCTIONS'),
            38: _('TOTAL TO PAY'),
            39: _('SERVICES SUBJECT TO WITHHOLDING INDIVIDUALS'),
            40: _('SERVICES SUBJECT TO WITHHOLDING NON-PROFIT ENTITIES (Rule No. 01-11)'),
            41: _('TOTAL SERVICES SUBJECT TO WITHHOLDING TO INDIVIDUALS AND NON-PROFIT ENTITIES'),
            42: _('SERVICES SUBJECT TO COMPANY WITHHOLDING (Rule No. 07-09)'),
            43: _('SERVICES SUBJECT TO COMPANY WITHHOLDING (Rule No. 02-05 and 07-07)'),
            44: _('GOODS OR SERVICES SUBJECT TO WITHHOLDING TO TAXPAYERS UNDER THE RST (Operations Taxed at 18%)'),
            45: _('GOODS OR SERVICES SUBJECT TO WITHHOLDING TO TAXPAYERS UNDER THE RST (Operations Taxed at 16%)'),
            46: _('TOTAL GOODS OR SERVICES SUBJECT TO WITHHOLDING TO TAXPAYERS UNDER THE RST (Sum of boxes 44+45)'),
            47: _('ASSETS SUBJECT TO RETENTION OF PROOF OF PURCHASE '
                  '(Operations Taxed at 18%) (Rule No. 08-10 and 05-19)'),
            48: _('ASSETS SUBJECT TO RETENTION OF PROOF OF PURCHASE '
                  '(Operations Taxed at 16%) (Rule No. 08-10 and 05-19)'),
            49: _('TOTAL ASSETS SUBJECT TO RETENTION PROOF OF PURCHASE'),
            50: _('ITBIS FOR SERVICES SUBJECT TO WITHHOLDING INDIVIDUALS AND NON-PROFIT ENTITIES'),
            51: _('ITBIS FOR SERVICES SUBJECT TO COMPANY WITHHOLDING (18% of box 42)'),
            52: _('ITBIS FOR SERVICES SUBJECT TO COMPANY WITHHOLDING (18% of box 43 for 0.30)'),
            53: _('ITBIS WITHHOLDED FROM TAXPAYERS UNDER THE RST (18% of box 44)'),
            54: _('ITBIS WITHHOLDED FROM TAXPAYERS UNDER THE RST (16% of box 45)'),
            55: _('TOTAL ITBIS WITHHOLDED FROM TAXPAYERS UNDER THE RST (Sum of boxes 53+54)'),
            56: _('ITBIS FOR GOODS SUBJECT TO RETENTION OF PROOF OF PURCHASE (18% of box 47) '
                  '(Rule No. 08-10 and 05-19)'),
            57: _('ITBIS FOR GOODS SUBJECT TO RETENTION OF PROOF OF PURCHASE (16% of box 48) '
                  '(Rule No. 08-10 and 05-19)'),
            58: _('TOTAL FOR ASSETS SUBJECT TO WITHHOLDING PROOF OF PURCHASE (Sum of boxes 56+57)'),
            59: _('TOTAL ITBIS RECEIVED FOR SALE'),
            60: _('TAX TO PAY (Sum of boxes 50+51+52+55+58+59)'),
            61: _('COMPUTABLE PAYMENTS ON ACCOUNT'),
            62: _('DIFFERENCE TO PAY (If the value of boxes 60-61 is Positive)'),
            63: _('NEW BALANCE IN FAVOR (If the value of boxes 60-61 is Negative)'),
            64: _('SURCHARGES'),
            65: _('COMPENSATION INTEREST'),
            66: _('SANCTIONS'),
            67: _('TOTAL TO PAY (Sum of boxes 62+64+65+66)'),
            68: _('GRAND TOTAL (Sum of boxes 38+67)')
        }

        for key, value in names.items():
            report_lines.update({
                key: {
                    'name': value,
                    'sequence': key,
                    'dgii_report_id': self.id,
                    'section': '6',
                    'coefficient': 0,
                    'quantity': 0,
                    'local_purchase': 0,
                    'services': 0,
                    'imports': 0,
                    'amount': 0,
                }
            })

        # Titles
        report_lines.update({
            'IT1II': {
                'name': _('II. INCOME FROM OPERATIONS'),
                'display_type': 'line_section',
                'sequence': 0,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1IIA': {
                'name': _('II.A NOT TAXED'),
                'display_type': 'line_section',
                'sequence': 2,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1IIB': {
                'name': _('II.B TAXED'),
                'display_type': 'line_section',
                'sequence': 10,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1III': {
                'name': _('III. SETTLEMENT'),
                'display_type': 'line_section',
                'sequence': 16,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1IV': {
                'name': _('IV. PENALTIES'),
                'display_type': 'line_section',
                'sequence': 35,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1V': {
                'name': _('V. AMOUNT TO PAY'),
                'display_type': 'line_section',
                'sequence': 38,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1VA': {
                'name': _('A. RETAINED / ITBIS PERCEIVED'),
                'display_type': 'line_section',
                'sequence': 39,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1B': {
                'name': _('B. PENALTIES'),
                'display_type': 'line_section',
                'sequence': 64,
                'dgii_report_id': self.id,
                'section': '6'
            },
            'IT1C': {
                'name': _('C. AMOUNT TO PAY'),
                'display_type': 'line_section',
                'sequence': 67,
                'dgii_report_id': self.id,
                'section': '6'
            },
        })

        return report_lines
    
    def _get_move_lines_it1(self, box):
        domain = [
            ('move_id.state', '=', 'posted'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ]
        domain += [('account_id.box_attachment_a', '=', box)] if 'A' in box else [('account_id.box_it1', '=', box)]
        
        # Not subjet to proportionality
        if box in ['A49c', 'A49s', 'A49i', 'A50c', 'A50s', 'A50i', 'A51c', 'A51s', 'A51i']:
            domain += [('move_id.l10n_do_is_subject_to_proportionality', '=', False)]

        return self.env['account.move.line'].search(domain)
    
    def get_ncf_type_dic(self):
        return {
            'B01': 1,
            'E31': 1,
            'B02': 2,
            'B03': 3,
            'B04': 4,
            'E34': 4,
            'B12': 5,
            'B14': 6,
            'B15': 7,
            'B16': 8,
        }

    def get_income_type_dic(self):
        return{
            '01': 20,
            '02': 21,
            '03': 22,
            '04': 23,
            '05': 24,
            '06': 25
        }

    # IT1
    
    def _compute_attachment_a_and_it1_data(self):
        box_ncf_type = self.get_ncf_type_dic()
        box_income_type = self.get_income_type_dic()

        self.env['dgii.reports.it1.line'].search([('dgii_report_id', 'in', self.ids)]).unlink()
        itbis_tax_objs = self.env['account.tax'].search([
            ('l10n_do_tax_type', '=', 'itbis')
        ])
        itbis_repartition_line_tax = itbis_tax_objs.mapped('invoice_repartition_line_ids') + itbis_tax_objs.mapped('refund_repartition_line_ids')

        for rec in self:

            attachment_a_lines = rec._get_attachment_a_dictionary()
            it1_lines = rec._get_it1_dictionary()
            sale_invoices = self.env['dgii.reports.sale.line'].search([('dgii_report_id', '=', rec.id)])
            purchase_invoices = self.env['dgii.reports.purchase.line'].search([('dgii_report_id', '=', rec.id)])
            month = rec.start_date.month - 1
            year = rec.start_date.year

            month = month % 12
            if month == 0:
                month = 12
                year -= 1

            datetime_month_before = rec.start_date.replace(month=month, year=year)
            previous_report = self.search([
                    ('company_id', '=', rec.company_id.id),
                    ('state', 'in', ('sent', 'generated')),
                    ('name', '=', '{}/{}'.format(datetime_month_before.month, datetime_month_before.year))
                ],
                limit=1
            )

            for sale_invoice in sale_invoices:

                # AII                    
                ncf_type = sale_invoice.invoice_id.fiscal_type_id.prefix
                
                if ncf_type not in box_ncf_type:
                    raise ValidationError(
                        _("""The NCF type '%s' for fiscal type '%s' is not configured in box_ncf_type. 
                            Please check your configuration.") % (ncf_type, fiscal_type_name)"""))
                
                attachment_a_lines[box_ncf_type[ncf_type]]['quantity'] += 1
                attachment_a_lines[box_ncf_type[ncf_type]]['amount'] += \
                    sale_invoice.invoice_id.amount_untaxed_signed
                attachment_a_lines[box_ncf_type[ncf_type]]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)

                # AIII
                sign_for_AII = 1 if sale_invoice.invoice_id.move_type != 'out_refund' else -1
                
                attachment_a_line_12_amount = sale_invoice.cash * sign_for_AII
                
                if attachment_a_line_12_amount != 0:
                    attachment_a_lines[12]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                    
                attachment_a_lines[12]['amount'] += attachment_a_line_12_amount
                    
                attachment_a_line_13_amount = sale_invoice.bank * sign_for_AII
                
                if attachment_a_line_13_amount != 0:
                    attachment_a_lines[13]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                
                attachment_a_lines[13]['amount'] += attachment_a_line_13_amount

                attachment_a_line_14_amount = sale_invoice.card * sign_for_AII
                
                if attachment_a_line_14_amount != 0:
                    attachment_a_lines[14]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                
                attachment_a_lines[14]['amount'] += attachment_a_line_14_amount

                attachment_a_line_15_amount = sale_invoice.credit * sign_for_AII
                
                if attachment_a_line_15_amount != 0:
                    attachment_a_lines[15]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                
                attachment_a_lines[15]['amount'] += attachment_a_line_15_amount

                attachment_a_line_16_amount = sale_invoice.bond * sign_for_AII
                
                if attachment_a_line_16_amount != 0:
                    attachment_a_lines[16]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                    
                attachment_a_lines[16]['amount'] += attachment_a_line_16_amount

                attachment_a_line_17_amount = sale_invoice.swap * sign_for_AII
                
                if attachment_a_line_17_amount != 0:
                    attachment_a_lines[17]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                    
                attachment_a_lines[17]['amount'] += attachment_a_line_17_amount

                attachment_a_line_18_amount = sale_invoice.others * sign_for_AII
                
                if attachment_a_line_18_amount != 0:
                    attachment_a_lines[18]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                    
                attachment_a_lines[18]['amount'] += attachment_a_line_18_amount

                # AIV
                attachment_a_lines[box_income_type[sale_invoice.invoice_id.income_type]]['amount'] += \
                    sale_invoice.invoiced_amount * sign_for_AII
                attachment_a_lines[box_income_type[sale_invoice.invoice_id.income_type]]['invoice_ids'][0][2].append(sale_invoice.invoice_id.id)
                
                # AVIII
                if sale_invoice.invoice_id.move_type == 'out_refund':

                    date_30_days_before = sale_invoice.invoice_id.date + timedelta(days=-30)

                    origin = self.env['account.move'].search([
                        ('ref', '=', sale_invoice.invoice_id.origin_out),
                        ('invoice_date', '<', date_30_days_before)
                    ], limit=1)

                    attachment_a_lines[43]['amount'] += abs(sale_invoice.invoiced_amount) if origin else 0

                #IT1-II.B

                for invoice_line in sale_invoice.invoice_id._get_tax_line_ids().filtered(
                        lambda tl: tl.tax_line_id.l10n_do_tax_type == 'itbis'):

                    tax_base_amount = invoice_line.tax_base_amount \
                        if sale_invoice.invoice_id.move_type != 'out_refund' else invoice_line.tax_base_amount * -1

                    if invoice_line.tax_line_id.amount == 18.0:
                        it1_lines[11]['amount'] += tax_base_amount
                    elif invoice_line.tax_line_id.amount == 16.0:
                        it1_lines[12]['amount'] += tax_base_amount
                    elif invoice_line.tax_line_id.amount == 9.0:
                        it1_lines[13]['amount'] += tax_base_amount
                    elif invoice_line.tax_line_id.amount == 8.0:
                        it1_lines[14]['amount'] += tax_base_amount
            
            attachment_a_lines_53_move_line_ids = []
            for purchase_invoice in purchase_invoices:

                # AVIII
                if purchase_invoice.invoice_id.fiscal_type_id.prefix in ('B14', 'E44'):
                    attachment_a_lines[44]['amount'] += purchase_invoice.invoice_id.amount_untaxed

                # IXc
                for invoice_line in purchase_invoice.filtered(
                    lambda i: i.invoice_id.l10n_do_is_subject_to_proportionality).mapped('invoice_id').mapped('invoice_line_ids'):

                    total_itbis_line = sum(
                        tax_values['balance']
                        for tax_key, tax_values in invoice_line.compute_all_tax.items()
                        if tax_key.get('tax_repartition_line_id', 0) in itbis_repartition_line_tax.ids
                    )
                    
                    if not invoice_line.product_id or invoice_line.product_id.type == 'service':
                        attachment_a_lines[53]['services'] += total_itbis_line

                    else:
                        attachment_a_lines[53]['local_purchase'] += total_itbis_line

                    if total_itbis_line:
                        attachment_a_lines_53_move_line_ids.append(invoice_line.id)


            # AII
            attachment_a_lines_9 = rec._get_move_lines_it1('A9')
            attachment_a_lines[9]['amount'] = abs(sum(attachment_a_lines_9.mapped('balance')))
            attachment_a_lines[9]['quantity'] = len(attachment_a_lines_9)
            attachment_a_lines[9]['move_line_ids'] = [(6, 0, attachment_a_lines_9.ids)] if attachment_a_lines_9 else False
            
            attachment_a_lines_10 = rec._get_move_lines_it1('A10')
            attachment_a_lines[10]['amount'] = abs(sum(attachment_a_lines_10.mapped('balance')))
            attachment_a_lines[10]['quantity'] = len(attachment_a_lines_10)
            attachment_a_lines[10]['move_line_ids'] = [(6, 0, attachment_a_lines_10.ids)] if attachment_a_lines_10 else False
            
            attachment_a_lines[11]['amount'] = sum([attachment_a_lines[box]['amount'] for box in range(1, 11)])
            attachment_a_lines[11]['quantity'] = sum([attachment_a_lines[box]['quantity'] for box in range(1, 11)])
            
            # AIII
            attachment_a_lines[19]['amount'] = sum([attachment_a_lines[box]['amount'] for box in range(12, 19)])

            # AIV
            attachment_a_lines[26]['amount'] = sum([attachment_a_lines[box]['amount'] for box in range(20, 26)])

            # AV
            attachment_a_lines_27 = rec._get_move_lines_it1('A27')
            attachment_a_lines[27]['amount'] = abs(sum(attachment_a_lines_27.mapped('balance')))
            attachment_a_lines[27]['move_line_ids'] = [(6, 0, attachment_a_lines_27.ids)] if attachment_a_lines_27 else False

            attachment_a_lines_28 = rec._get_move_lines_it1('A28')
            attachment_a_lines[28]['amount'] = abs(sum(attachment_a_lines_28.mapped('balance')))
            attachment_a_lines[28]['move_line_ids'] = [(6, 0, attachment_a_lines_28.ids)] if attachment_a_lines_28 else False
            
            attachment_a_lines_29 = rec._get_move_lines_it1('A29')
            attachment_a_lines[29]['amount'] = abs(sum(attachment_a_lines_29.mapped('balance')))
            attachment_a_lines[29]['move_line_ids'] = [(6, 0, attachment_a_lines_29.ids)] if attachment_a_lines_29 else False

            attachment_a_lines_30 = rec._get_move_lines_it1('A30')
            attachment_a_lines[30]['amount'] = abs(sum(attachment_a_lines_30.mapped('balance')))
            attachment_a_lines[30]['move_line_ids'] = [(6, 0, attachment_a_lines_30.ids)] if attachment_a_lines_30 else False

            attachment_a_lines_31 = rec._get_move_lines_it1('A31')
            attachment_a_lines[31]['amount'] = abs(sum(attachment_a_lines_31.mapped('balance')))
            attachment_a_lines[31]['move_line_ids'] = [(6, 0, attachment_a_lines_31.ids)] if attachment_a_lines_31 else False

            attachment_a_lines_32 = rec._get_move_lines_it1('A32')
            attachment_a_lines[32]['amount'] = abs(sum(attachment_a_lines_32.mapped('balance')))
            attachment_a_lines[32]['move_line_ids'] = [(6, 0, attachment_a_lines_32.ids)] if attachment_a_lines_32 else False
            
            attachment_a_lines[33]['amount'] = sum([attachment_a_lines[box]['amount'] for box in range(27, 33)])

            # AVI
            attachment_a_lines_34 = rec._get_move_lines_it1('A34')
            attachment_a_lines[34]['local_purchase'] = abs(sum(attachment_a_lines_34.mapped('balance')))
            attachment_a_lines[34]['move_line_ids'] = [(6, 0, attachment_a_lines_34.ids)] if attachment_a_lines_34 else False
            attachment_a_lines[34]['amount'] = attachment_a_lines[34]['local_purchase'] * 0.10

            attachment_a_lines_35 = rec._get_move_lines_it1('A35')
            attachment_a_lines[35]['local_purchase'] = abs(sum(attachment_a_lines_35.mapped('balance')))
            attachment_a_lines[35]['move_line_ids'] = [(6, 0, attachment_a_lines_35.ids)] if attachment_a_lines_35 else False
            # TODO: missing boxes: attachment_a_lines[35]['amount'], attachment_a_lines[39]['amount'] and
            #  attachment_a_lines[40]['amount']
            # attachment_a_lines[35]['amount'] =

            attachment_a_lines_36 = rec._get_move_lines_it1('A36')
            attachment_a_lines[36]['amount'] = abs(sum(attachment_a_lines_36.mapped('balance')))
            attachment_a_lines[36]['move_line_ids'] = [(6, 0, attachment_a_lines_36.ids)] if attachment_a_lines_36 else False

            attachment_a_lines[37]['local_purchase'] = attachment_a_lines[34]['local_purchase'] + \
                                                    attachment_a_lines[35]['local_purchase']
            attachment_a_lines[37]['amount'] = attachment_a_lines[34]['amount'] + \
                                            attachment_a_lines[35]['amount'] + \
                                            attachment_a_lines[36]['amount']
            attachment_a_lines[38]['amount'] = attachment_a_lines[37]['local_purchase'] - \
                                            attachment_a_lines[37]['amount']
            # AVII
            attachment_a_lines_39 = rec._get_move_lines_it1('A39')
            attachment_a_lines[39]['local_purchase'] = abs(sum(attachment_a_lines_39.mapped('balance')))
            # attachment_a_lines[39]['amount'] =
            attachment_a_lines[39]['move_line_ids'] = [(6, 0, attachment_a_lines_36.ids)] if attachment_a_lines_39 else False

            attachment_a_lines_40 = rec._get_move_lines_it1('A40')
            attachment_a_lines[40]['local_purchase'] = abs(sum(attachment_a_lines_40.mapped('balance')))
            # attachment_a_lines[40]['amount'] =
            attachment_a_lines[40]['move_line_ids'] = [(6, 0, attachment_a_lines_40.ids)] if attachment_a_lines_40 else False

            attachment_a_lines[41]['local_purchase'] = attachment_a_lines[39]['local_purchase'] + \
                                                    attachment_a_lines[40]['local_purchase']
            attachment_a_lines[41]['amount'] = attachment_a_lines[39]['amount'] + attachment_a_lines[40]['amount']
            attachment_a_lines[42]['amount'] = attachment_a_lines[41]['local_purchase'] - \
                                            attachment_a_lines[41]['amount']

            # AIXa
            attachment_a_lines_45c = rec._get_move_lines_it1('A45c')
            attachment_a_lines_45s = rec._get_move_lines_it1('A45s')
            attachment_a_lines_45i = rec._get_move_lines_it1('A45i')
            attachment_a_lines[45]['local_purchase'] = abs(sum(attachment_a_lines_45c.mapped('balance')))
            attachment_a_lines[45]['services'] = abs(sum(attachment_a_lines_45s.mapped('balance')))
            attachment_a_lines[45]['imports'] = abs(sum(attachment_a_lines_45i.mapped('balance')))
            attachment_a_lines[45]['move_line_ids'] = [(6, 0, attachment_a_lines_45c.ids + attachment_a_lines_45s.ids + attachment_a_lines_45i.ids)] if attachment_a_lines_45c or attachment_a_lines_45s or attachment_a_lines_45i else False
            attachment_a_lines[45]['amount'] = attachment_a_lines[45]['local_purchase'] + \
                                            attachment_a_lines[45]['services'] + \
                                            attachment_a_lines[45]['imports']
            
            attachment_a_lines_46c = rec._get_move_lines_it1('A46c')
            attachment_a_lines_46s = rec._get_move_lines_it1('A46s')
            attachment_a_lines_46i = rec._get_move_lines_it1('A46i')
            attachment_a_lines[46]['local_purchase'] = abs(sum(attachment_a_lines_46c.mapped('balance')))
            attachment_a_lines[46]['services'] = abs(sum(attachment_a_lines_46s.mapped('balance')))
            attachment_a_lines[46]['imports'] = abs(sum(attachment_a_lines_46i.mapped('balance')))
            attachment_a_lines[46]['move_line_ids'] = [(6, 0, attachment_a_lines_46c.ids + attachment_a_lines_46s.ids + attachment_a_lines_46i.ids)] if attachment_a_lines_46c or attachment_a_lines_46s or attachment_a_lines_46i else False
            attachment_a_lines[46]['amount'] = attachment_a_lines[46]['local_purchase'] + \
                                            attachment_a_lines[46]['services'] + \
                                            attachment_a_lines[46]['imports']
            
            attachment_a_lines_47c = rec._get_move_lines_it1('A47c')
            attachment_a_lines_47s = rec._get_move_lines_it1('A47s')
            attachment_a_lines_47i = rec._get_move_lines_it1('A47i')
            attachment_a_lines[47]['local_purchase'] = abs(sum(attachment_a_lines_47c.mapped('balance')))
            attachment_a_lines[47]['services'] = abs(sum(attachment_a_lines_47s.mapped('balance')))
            attachment_a_lines[47]['imports'] = abs(sum(attachment_a_lines_47i.mapped('balance')))
            attachment_a_lines[47]['move_line_ids'] = [(6, 0, attachment_a_lines_47c.ids + attachment_a_lines_47s.ids + attachment_a_lines_47i.ids)] if attachment_a_lines_47c or attachment_a_lines_47s or attachment_a_lines_47i else False
            attachment_a_lines[47]['amount'] = attachment_a_lines[47]['local_purchase'] + \
                                            attachment_a_lines[47]['services'] + \
                                            attachment_a_lines[47]['imports']
            
            attachment_a_lines[48]['local_purchase'] = sum([
                attachment_a_lines[box]['local_purchase'] for box in range(45, 48)])
            attachment_a_lines[48]['services'] = sum([
                attachment_a_lines[box]['services'] for box in range(45, 48)])
            attachment_a_lines[48]['imports'] = sum([
                attachment_a_lines[box]['imports'] for box in range(45, 48)])
            attachment_a_lines[48]['amount'] = attachment_a_lines[48]['local_purchase'] + \
                                            attachment_a_lines[48]['services'] + \
                                            attachment_a_lines[48]['imports']

            # AIXb
            attachment_a_lines_49c = rec._get_move_lines_it1('A49c')
            attachment_a_lines_49s = rec._get_move_lines_it1('A49s')
            attachment_a_lines_49i = rec._get_move_lines_it1('A49i')
            attachment_a_lines[49]['local_purchase'] = abs(sum(attachment_a_lines_49c.mapped('balance')))
            attachment_a_lines[49]['services'] = abs(sum(attachment_a_lines_49s.mapped('balance')))
            attachment_a_lines[49]['imports'] = abs(sum(attachment_a_lines_49i.mapped('balance')))
            attachment_a_lines[49]['move_line_ids'] = [(6, 0, attachment_a_lines_49c.ids + attachment_a_lines_49s.ids + attachment_a_lines_49i.ids)] if attachment_a_lines_49c or attachment_a_lines_49s or attachment_a_lines_49i else False
            attachment_a_lines[49]['amount'] = attachment_a_lines[49]['local_purchase'] + \
                                            attachment_a_lines[49]['services'] + \
                                            attachment_a_lines[49]['imports']

            attachment_a_lines_50c = rec._get_move_lines_it1('A50c')
            attachment_a_lines_50s = rec._get_move_lines_it1('A50s')
            attachment_a_lines_50i = rec._get_move_lines_it1('A50i')
            attachment_a_lines[50]['local_purchase'] = abs(sum(attachment_a_lines_50c.mapped('balance')))
            attachment_a_lines[50]['services'] = abs(sum(attachment_a_lines_50s.mapped('balance')))
            attachment_a_lines[50]['imports'] = abs(sum(attachment_a_lines_50i.mapped('balance')))
            attachment_a_lines[50]['move_line_ids'] = [(6, 0, attachment_a_lines_50c.ids + attachment_a_lines_50s.ids + attachment_a_lines_50i.ids)] if attachment_a_lines_50c or attachment_a_lines_50s or attachment_a_lines_50i else False
            attachment_a_lines[50]['amount'] = attachment_a_lines[50]['local_purchase'] + \
                                            attachment_a_lines[50]['services'] + \
                                            attachment_a_lines[50]['imports']
            
            attachment_a_lines_51c = rec._get_move_lines_it1('A51c')
            attachment_a_lines_51s = rec._get_move_lines_it1('A51s')
            attachment_a_lines_51i = rec._get_move_lines_it1('A51i')
            attachment_a_lines[51]['local_purchase'] = abs(sum(attachment_a_lines_51c.mapped('balance')))
            attachment_a_lines[51]['services'] = abs(sum(attachment_a_lines_51s.mapped('balance')))
            attachment_a_lines[51]['imports'] = abs(sum(attachment_a_lines_51i.mapped('balance')))
            attachment_a_lines[51]['move_line_ids'] = [(6, 0, attachment_a_lines_51c.ids + attachment_a_lines_51s.ids + attachment_a_lines_51i.ids)] if attachment_a_lines_51c or attachment_a_lines_51s or attachment_a_lines_51i else False
            attachment_a_lines[51]['amount'] = attachment_a_lines[51]['local_purchase'] + \
                                            attachment_a_lines[51]['services'] + \
                                            attachment_a_lines[51]['imports']

            attachment_a_lines[52]['local_purchase'] = sum([
                attachment_a_lines[box]['local_purchase'] for box in range(49, 53)])
            attachment_a_lines[52]['services'] = sum([
                attachment_a_lines[box]['services'] for box in range(49, 53)])
            attachment_a_lines[52]['imports'] = sum([
                attachment_a_lines[box]['imports'] for box in range(49, 53)])
            attachment_a_lines[52]['amount'] = attachment_a_lines[52]['local_purchase'] + \
                                            attachment_a_lines[52]['services'] + \
                                            attachment_a_lines[52]['imports']
                                            

            # AIXc
            attachment_a_lines_53 = rec._get_move_lines_it1('A53')
            attachment_a_lines[53]['imports'] = abs(sum(attachment_a_lines_53.mapped('balance')))
            attachment_a_lines_53_move_line_ids += attachment_a_lines_53.ids
            attachment_a_lines[53]['move_line_ids'] = [(6, 0, attachment_a_lines_53_move_line_ids)] if attachment_a_lines_53_move_line_ids else False
            attachment_a_lines[53]['amount'] = attachment_a_lines[53]['local_purchase'] + \
                                            attachment_a_lines[53]['services'] + \
                                            attachment_a_lines[53]['imports']

            # IT1II
            it1_lines[1]['amount'] = attachment_a_lines[11]['amount']

            # IT1IIA
            it1_lines_2 = rec._get_move_lines_it1('I2')
            it1_lines[2]['amount'] = abs(sum(it1_lines_2.mapped('balance')))
            it1_lines[2]['move_line_ids'] = [(6, 0, it1_lines_2.ids)] if it1_lines_2 else False

            it1_lines_3 = rec._get_move_lines_it1('I3')
            it1_lines[3]['amount'] = abs(sum(it1_lines_3.mapped('balance')))
            it1_lines[3]['move_line_ids'] = [(6, 0, it1_lines_3.ids)] if it1_lines_3 else False

            it1_lines_4 = rec._get_move_lines_it1('I4')
            it1_lines[4]['amount'] = abs(sum(it1_lines_4.mapped('balance')))
            it1_lines[4]['move_line_ids'] = [(6, 0, it1_lines_4.ids)] if it1_lines_4 else False

            it1_lines_5 = rec._get_move_lines_it1('I5')
            it1_lines[5]['amount'] = abs(sum(it1_lines_5.mapped('balance')))
            it1_lines[5]['move_line_ids'] = [(6, 0, it1_lines_5.ids)] if it1_lines_5 else False

            it1_lines[6]['amount'] = attachment_a_lines[38]['amount']

            it1_lines[7]['amount'] = attachment_a_lines[42]['amount']

            it1_lines_8 = rec._get_move_lines_it1('I8')
            it1_lines[8]['amount'] = abs(sum(it1_lines_8.mapped('balance')))
            it1_lines[8]['move_line_ids'] = [(6, 0, it1_lines_8.ids)] if it1_lines_8 else False

            it1_lines[9]['amount'] = sum([it1_lines[box]['amount'] for box in range(2, 9)])

            # IT1IIB
            it1_lines[10]['amount'] = it1_lines[1]['amount'] - it1_lines[9]['amount']

            it1_lines_15 = rec._get_move_lines_it1('I15')
            it1_lines[15]['amount'] = abs(sum(it1_lines_15.mapped('balance')))
            it1_lines[15]['move_line_ids'] = [(6, 0, it1_lines_15.ids)] if it1_lines_15 else False
            
            attachment_a_lines[54]['coefficient'] = (it1_lines[2]['amount'] +
                                                    it1_lines[5]['amount'] +
                                                    it1_lines[10]['amount']) / (it1_lines[1]['amount']) \
                if it1_lines[1]['amount'] != 0 else 0

            attachment_a_lines[55]['local_purchase'] = attachment_a_lines[53]['local_purchase'] * \
                                                    attachment_a_lines[54]['coefficient']
            attachment_a_lines[55]['services'] = attachment_a_lines[53]['services'] * \
                                                attachment_a_lines[54]['coefficient']
            attachment_a_lines[55]['imports'] = attachment_a_lines[53]['imports'] * \
                                                attachment_a_lines[54]['coefficient']
            attachment_a_lines[55]['amount'] = attachment_a_lines[53]['amount'] * attachment_a_lines[54]['coefficient']

            attachment_a_lines[56]['local_purchase'] = attachment_a_lines[52]['local_purchase'] + \
                                                    attachment_a_lines[55]['local_purchase']
            attachment_a_lines[56]['services'] = attachment_a_lines[52]['services'] + attachment_a_lines[55]['services']
            attachment_a_lines[56]['imports'] = attachment_a_lines[52]['imports'] + attachment_a_lines[55]['imports']
            attachment_a_lines[56]['amount'] = attachment_a_lines[52]['amount'] + attachment_a_lines[55]['amount']

            # IT1III
            it1_lines[16]['amount'] = it1_lines[11]['amount'] * 0.18
            it1_lines[17]['amount'] = it1_lines[12]['amount'] * 0.16
            it1_lines[18]['amount'] = it1_lines[13]['amount'] * 0.09
            it1_lines[19]['amount'] = it1_lines[14]['amount'] * 0.08
            it1_lines[20]['amount'] = it1_lines[15]['amount'] * 0.18
            it1_lines[21]['amount'] = sum([it1_lines[box]['amount'] for box in range(16, 21)])
            it1_lines[22]['amount'] = attachment_a_lines[56]['local_purchase']
            it1_lines[23]['amount'] = attachment_a_lines[56]['services']
            it1_lines[24]['amount'] = attachment_a_lines[56]['imports']
            it1_lines[25]['amount'] = sum([it1_lines[box]['amount'] for box in range(22, 25)])
            it1_lines[26]['amount'] = it1_lines[21]['amount'] - it1_lines[25]['amount'] \
                if it1_lines[25]['amount'] < it1_lines[21]['amount'] else 0
            it1_lines[27]['amount'] = abs(it1_lines[21]['amount'] - it1_lines[25]['amount']) \
                if it1_lines[25]['amount'] > it1_lines[21]['amount'] else 0

            it1_lines_28 = rec._get_move_lines_it1('I28')
            it1_lines[28]['amount'] = abs(sum(it1_lines_28.mapped('balance')))
            it1_lines[28]['move_line_ids'] = [(6, 0, it1_lines_28.ids)] if it1_lines_28 else False

            previous_it1_line_34_obj = self.env['dgii.reports.it1.line'].search([
                ('dgii_report_id', '=', previous_report.id if previous_report else 0),
                ('sequence', '=', 34),
                ('section', '=', '6'),
            ])

            it1_lines[29]['amount'] = previous_it1_line_34_obj.amount if previous_it1_line_34_obj else 0
            it1_lines[30]['amount'] = attachment_a_lines[33]['amount']

            it1_lines_31 = rec._get_move_lines_it1('I31')
            it1_lines[31]['amount'] = abs(sum(it1_lines_31.mapped('balance')))
            it1_lines[31]['move_line_ids'] = [(6, 0, it1_lines_31.ids)] if it1_lines_31 else False

            it1_lines_32 = rec._get_move_lines_it1('I32')
            it1_lines[32]['amount'] = abs(sum(it1_lines_32.mapped('balance')))
            it1_lines[32]['move_line_ids'] = [(6, 0, it1_lines_32.ids)] if it1_lines_32 else False

            it1_line_33_34 = it1_lines[26]['amount'] - \
                        it1_lines[28]['amount'] - \
                        it1_lines[29]['amount'] - \
                        it1_lines[30]['amount'] - \
                        it1_lines[31]['amount'] - \
                        it1_lines[32]['amount']

            it1_lines[33]['amount'] = it1_line_33_34 if it1_line_33_34 > 0 else 0
            it1_lines[34]['amount'] = sum([it1_lines[box]['amount'] for box in range(27, 33)]) \
                if it1_line_33_34 < 0 else 0

            # IT1IV
            it1_lines_35 = rec._get_move_lines_it1('I35')
            it1_lines[35]['amount'] = abs(sum(it1_lines_35.mapped('balance')))
            it1_lines[35]['move_line_ids'] = [(6, 0, it1_lines_35.ids)] if it1_lines_35 else False

            it1_lines_36 = rec._get_move_lines_it1('I36')
            it1_lines[36]['amount'] = abs(sum(it1_lines_36.mapped('balance')))
            it1_lines[36]['move_line_ids'] = [(6, 0, it1_lines_36.ids)] if it1_lines_36 else False

            it1_lines_37 = rec._get_move_lines_it1('I37')
            it1_lines[37]['amount'] = abs(sum(it1_lines_37.mapped('balance')))
            it1_lines[37]['move_line_ids'] = [(6, 0, it1_lines_37.ids)] if it1_lines_37 else False

            # IT1V
            it1_lines[38]['amount'] = it1_lines[33]['amount'] + \
                                    it1_lines[35]['amount'] + \
                                    it1_lines[36]['amount'] + \
                                    it1_lines[37]['amount']

            # IT1A
            it1_lines_39 = rec._get_move_lines_it1('I39')
            it1_lines[39]['amount'] = abs(sum(it1_lines_39.mapped('balance')))
            it1_lines[39]['move_line_ids'] = [(6, 0, it1_lines_39.ids)] if it1_lines_39 else False

            it1_lines_40 = rec._get_move_lines_it1('I40')
            it1_lines[40]['amount'] = abs(sum(it1_lines_40.mapped('balance')))
            it1_lines[40]['move_line_ids'] = [(6, 0, it1_lines_40.ids)] if it1_lines_40 else False

            it1_lines[41]['amount'] = it1_lines[39]['amount'] + it1_lines[40]['amount']

            it1_lines_42 = rec._get_move_lines_it1('I42')
            it1_lines[42]['amount'] = abs(sum(it1_lines_42.mapped('balance')))
            it1_lines[42]['move_line_ids'] = [(6, 0, it1_lines_42.ids)] if it1_lines_42 else False

            it1_lines_43 = rec._get_move_lines_it1('I43')
            it1_lines[43]['amount'] = abs(sum(it1_lines_43.mapped('balance')))
            it1_lines[43]['move_line_ids'] = [(6, 0, it1_lines_43.ids)] if it1_lines_43 else False

            it1_lines_44 = rec._get_move_lines_it1('I44')
            it1_lines[44]['amount'] = abs(sum(it1_lines_44.mapped('balance')))
            it1_lines[44]['move_line_ids'] = [(6, 0, it1_lines_44.ids)] if it1_lines_44 else False

            it1_lines_45 = rec._get_move_lines_it1('I45')
            it1_lines[45]['amount'] = abs(sum(it1_lines_45.mapped('balance')))
            it1_lines[45]['move_line_ids'] = [(6, 0, it1_lines_45.ids)] if it1_lines_45 else False
            
            it1_lines[46]['amount'] = it1_lines[44]['amount'] + it1_lines[45]['amount']

            it1_lines_47 = rec._get_move_lines_it1('I47')
            it1_lines[47]['amount'] = abs(sum(it1_lines_47.mapped('balance')))
            it1_lines[47]['move_line_ids'] = [(6, 0, it1_lines_47.ids)] if it1_lines_47 else False

            it1_lines_48 = rec._get_move_lines_it1('I48')
            it1_lines[48]['amount'] = abs(sum(it1_lines_48.mapped('balance')))
            it1_lines[48]['move_line_ids'] = [(6, 0, it1_lines_48.ids)] if it1_lines_48 else False

            it1_lines[49]['amount'] = it1_lines[47]['amount'] + it1_lines[48]['amount']

            it1_lines[50]['amount'] = it1_lines[41]['amount'] * 0.18

            it1_lines[51]['amount'] = it1_lines[42]['amount'] * 0.18

            it1_lines[52]['amount'] = it1_lines[43]['amount'] * 0.18 * 0.30

            it1_lines[53]['amount'] = it1_lines[44]['amount'] * 0.18

            it1_lines[54]['amount'] = it1_lines[45]['amount'] * 0.16

            it1_lines[55]['amount'] = it1_lines[53]['amount'] + it1_lines[54]['amount']

            it1_lines[56]['amount'] = it1_lines[47]['amount'] * 0.18

            it1_lines[57]['amount'] = it1_lines[48]['amount'] * 0.16

            it1_lines[58]['amount'] = it1_lines[56]['amount'] + it1_lines[57]['amount']

            it1_lines_59 = rec._get_move_lines_it1('I59')
            it1_lines[59]['amount'] = abs(sum(it1_lines_59.mapped('balance')))
            it1_lines[59]['move_line_ids'] = [(6, 0, it1_lines_59.ids)] if it1_lines_59 else False

            it1_lines[60]['amount'] = it1_lines[50]['amount'] + \
                                    it1_lines[51]['amount'] + \
                                    it1_lines[52]['amount'] + \
                                    it1_lines[55]['amount'] + \
                                    it1_lines[58]['amount'] + \
                                    it1_lines[59]['amount']

            it1_lines_61 = rec._get_move_lines_it1('I61')
            it1_lines[61]['amount'] = abs(sum(it1_lines_61.mapped('balance')))
            it1_lines[61]['move_line_ids'] = [(6, 0, it1_lines_61.ids)] if it1_lines_61 else False

            it1_lines[62]['amount'] = abs(it1_lines[60]['amount'] - it1_lines[61]['amount']) \
                if it1_lines[60]['amount'] > it1_lines[61]['amount'] else 0

            it1_lines[63]['amount'] = abs(it1_lines[60]['amount'] - it1_lines[61]['amount']) \
                if it1_lines[60]['amount'] < it1_lines[61]['amount'] else 0
            
            it1_lines_64 = rec._get_move_lines_it1('I64')
            it1_lines[64]['amount'] = abs(sum(it1_lines_64.mapped('balance')))
            it1_lines[64]['move_line_ids'] = [(6, 0, it1_lines_64.ids)] if it1_lines_64 else False

            it1_lines_65 = rec._get_move_lines_it1('I65')
            it1_lines[65]['amount'] = abs(sum(it1_lines_65.mapped('balance')))
            it1_lines[65]['move_line_ids'] = [(6, 0, it1_lines_65.ids)] if it1_lines_65 else False

            it1_lines_66 = rec._get_move_lines_it1('I66')
            it1_lines[66]['amount'] = abs(sum(it1_lines_66.mapped('balance')))
            it1_lines[66]['move_line_ids'] = [(6, 0, it1_lines_66.ids)] if it1_lines_66 else False

            it1_lines[67]['amount'] = it1_lines[62]['amount'] + \
                                    it1_lines[64]['amount'] + \
                                    it1_lines[65]['amount'] + \
                                    it1_lines[66]['amount']
            it1_lines[68]['amount'] = it1_lines[38]['amount'] + it1_lines[67]['amount']

            self.env['dgii.reports.it1.line'].create(attachment_a_lines.values())
            self.env['dgii.reports.it1.line'].create(it1_lines.values())
    
    def _generate_report(self):

        self._compute_606_data()
        self._compute_607_data()
        self._compute_608_data()
        self._compute_609_data()
        self._compute_attachment_a_and_it1_data()
        
        if self.state != 'generated':
            self.state = 'generated'
        else:
            self.message_post(body=_('Report generated again.'))

    def generate_report(self):
        reports_without_sent = self.env['dgii.reports'].search([
            ('state', '!=', 'sent'),
            ('company_id', '=', self.company_id.id),
            ('end_date', '<', self.end_date)
        ])

        if reports_without_sent:
            raise ValidationError(
                _('There are reports that have not been sent yet. Please send them before generating a new one.'))

        if self.state == 'generated':
            action = self.env.ref(
                'dgii_reports.dgii_report_regenerate_wizard_action').read()[0]
            action['context'] = {'default_report_id': self.id}
            return action
        else:
            self._generate_report()
    
    def is_applicable_for_withholding(self, invoice):
        
        if (invoice.withholding_itbis != 0 or invoice.income_withholding != 0) and \
            invoice.payment_date and \
            invoice.payment_date >= self.start_date and \
            invoice.payment_date <= self.end_date:
            return True
        
        return False
    
    def has_pending_withholding(self, invoice):
        has_withholding = invoice.withholding_itbis != 0 or invoice.income_withholding != 0
        
        if has_withholding and not invoice.payment_date:
            return True
        elif has_withholding and invoice.payment_date and invoice.payment_date > self.end_date:
            return True

        return False

    def is_applicable_payment_date(self, invoice):
        if invoice.payment_date and invoice.payment_date <= self.end_date:
            return True
        return False

    
    def _invoice_status_sent(self):
        for report in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            SaleLine = self.env['dgii.reports.sale.line']
            CancelLine = self.env['dgii.reports.cancel.line']
            ExteriorLine = self.env['dgii.reports.exterior.line']
            invoice_ids = PurchaseLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += SaleLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += CancelLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += ExteriorLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')

            for inv in invoice_ids:                
                if self.has_pending_withholding(inv):
                    inv.fiscal_status = 'normal'
                else:
                    inv.fiscal_status = 'done'

    
    def state_sent(self):
        for report in self:
            report._invoice_status_sent()
            report.state = 'sent'

    def get_606_tree_view(self):
        return {
            'name': '606',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.purchase.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_report_purchase_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_607_tree_view(self):
        return {
            'name': '607',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.sale.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_report_sale_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_608_tree_view(self):
        return {
            'name': '608',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.cancel.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_cancel_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_609_tree_view(self):
        return {
            'name': '609',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.exterior.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_exterior_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }
    
class DgiiReportPurchaseLine(models.Model):
    _name = 'dgii.reports.purchase.line'
    _description = "DGII Reports Purchase Line"
    _order = 'line asc'

    dgii_report_id = fields.Many2one(
        comodel_name='dgii.reports', 
        ondelete='cascade', 
        index=True,
    )
    line = fields.Integer()

    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    expense_type = fields.Char(size=2)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    payment_date = fields.Date()
    service_total_amount = fields.Float()
    good_total_amount = fields.Float()
    invoiced_amount = fields.Float()
    invoiced_itbis = fields.Float()
    withholded_itbis = fields.Float()
    proportionality_tax = fields.Float()
    cost_itbis = fields.Float()
    advance_itbis = fields.Float()
    purchase_perceived_itbis = fields.Float()
    isr_withholding_type = fields.Char()
    income_withholding = fields.Float()
    purchase_perceived_isr = fields.Float()
    selective_tax = fields.Float()
    other_taxes = fields.Float()
    legal_tip = fields.Float()
    payment_type = fields.Char()

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move')
    credit_note = fields.Boolean()

    def action_view_invoice(self):
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.invoice_id.id
        return action


class DgiiReportSaleLine(models.Model):
    _name = 'dgii.reports.sale.line'
    _description = "DGII Reports Sale Line"

    dgii_report_id = fields.Many2one(
        comodel_name='dgii.reports', 
        ondelete='cascade', 
        index=True
    )
    line = fields.Integer()
    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    income_type = fields.Char()
    invoice_date = fields.Date()
    withholding_date = fields.Date()
    invoiced_amount = fields.Float()
    invoiced_itbis = fields.Float()
    third_withheld_itbis = fields.Float()
    perceived_itbis = fields.Float()
    third_income_withholding = fields.Float()
    perceived_isr = fields.Float()
    selective_tax = fields.Float()
    other_taxes = fields.Float()
    legal_tip = fields.Float()

    # Tipo de Venta/ Forma de pago
    cash = fields.Float()
    bank = fields.Float()
    card = fields.Float()
    credit = fields.Float()
    bond = fields.Float()
    swap = fields.Float()
    others = fields.Float()

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move')
    credit_note = fields.Boolean()

    def action_view_invoice(self):
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.invoice_id.id
        return action


class DgiiCancelReportLine(models.Model):
    _name = 'dgii.reports.cancel.line'
    _description = "DGII Reports Cancel Line"

    dgii_report_id = fields.Many2one(
        comodel_name='dgii.reports', 
        ondelete='cascade', 
        index=True
    )
    line = fields.Integer()

    fiscal_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    annulation_type = fields.Char(size=2)

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move')

    def action_view_invoice(self):
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.invoice_id.id
        return action


class DgiiExteriorReportLine(models.Model):
    _name = 'dgii.reports.exterior.line'
    _description = "DGII Reports Exterior Line"

    dgii_report_id = fields.Many2one(
        comodel_name='dgii.reports', 
        ondelete='cascade', 
        index=True,
    )
    line = fields.Integer()

    legal_name = fields.Char()
    tax_id_type = fields.Integer()
    tax_id = fields.Char()
    country_code = fields.Char()
    purchased_service_type = fields.Char(size=2)
    service_type_detail = fields.Char(size=2)
    related_part = fields.Integer()
    doc_number = fields.Char()
    doc_date = fields.Date()
    invoiced_amount = fields.Float()
    isr_withholding_date = fields.Date()
    presumed_income = fields.Float()
    withholded_isr = fields.Float()
    invoice_id = fields.Many2one('account.move')

    def action_view_invoice(self):
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.invoice_id.id
        return action

class DgiiReportsIt1(models.Model):
    _name = 'dgii.reports.it1.line'
    _description = "Attached a and IT-1 Report"
    _order = 'sequence,display_type,id'

    name = fields.Char(
        string='Name',
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    dgii_report_id = fields.Many2one(
        comodel_name='dgii.reports',
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='dgii_report_id.currency_id'
    )
    section = fields.Selection(
        string='section',
        selection=[
            # Attachment a
            ('1', 'Section 1'),
            ('2', 'Section 2'),
            ('3', 'Section 3'),
            ('4', 'Section 4'),
            ('5', 'Section 5'),

            # IT-1
            ('6', 'Section 6'),
        ],
        required=False,
    )
    coefficient = fields.Float(
        string='%',
    )
    quantity = fields.Integer(
        string='QUANTITY'
    )
    local_purchase = fields.Monetary(
        string="LOCAL PURCHASE",
    )
    services = fields.Monetary(
        string="SERVICES",
    )
    imports = fields.Monetary(
        string="IMPORTS",
    )
    amount = fields.Monetary(
        string="AMOUNT",
    )
    display_type = fields.Selection(
        string="Display type",
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False,
        help="Technical field for UX purpose.",
    )
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Move Lines',
    )
    invoice_ids = fields.Many2many(
        comodel_name='account.move',
        string='Invoices',
    )

