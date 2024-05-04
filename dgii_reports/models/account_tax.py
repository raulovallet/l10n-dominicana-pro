from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_do_tax_type = fields.Selection(
        selection=[
            ('itbis', 'ITBIS'),
            ('ritbis', 'ITBIS Withholding'),
            # TODO: investigate Subject to proportionality and ITBIS carried to cost
            #('prop', 'Subject to proportionality'),
            #('itbis_cost', 'ITBIS carried to cost'),
            ('isr', 'ISR Withholding'),
            ('isc', 'Selective Consumption Tax (SCT)'),
            ('other', 'Other taxes'),
            ('tip', 'Legal tip'),
            ('rext', 'Overseas payments (law 253-12)'),
            ('none', 'Non deductible')
        ],
        default="none",
        string="Tax DGII Type",
    )
    isr_retention_type = fields.Selection(
        selection=[
            ('01', 'Rentals'),
            ('02', 'Fees for Services'),
            ('03', 'Other Incomes'),
            ('04', 'Presumed Income'),
            ('05', 'Interest Paid to Legal Entities'),
            ('06', 'Interests Paid to Individuals'),
            ('07', 'Withholding by State Providers'),
            ('08', 'Mobile Games')
        ],
        string="ISR Withholding Type",
    )

