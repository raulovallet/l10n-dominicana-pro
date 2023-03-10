# Part of Domincana Premium. See LICENSE file for full copyright and
# licensing details.
# © 2018 José López <jlopez@indexa.do>

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    box_attachment_a = fields.Selection(
        string='Attachment A (IT1)',
        selection=[
            # AII
            ('A9', 'A9 - OTHER OPERATIONS (POSITIVE)'),
            ('A10', 'A10 - OTHER OPERATIONS (NEGATIVE)'),

            # AV
            ('A27', 'A27 - COMPUTABLE PAYMENTS FOR WITHHOLDINGS (Rule No. 08-04)'),
            ('A28', 'A28 - COMPUTABLE PAYMENTS FOR SALES OF AIR TRANSPORTATION TICKETS (Rule No. 02-05) (BSP-IATA)'),
            ('A29', 'A29 - COMPUTABLE PAYMENTS FOR OTHER WITHHOLDINGS (Rule No. 02-05)'),
            ('A30', 'A30 - COMPUTABLE PAYMENTS FOR SALES OF ACCOMMODATION AND OCCUPANCY PACKAGES'),
            ('A31', 'A31 - CREDIT FOR WITHHOLDING BY STATE ENTITIES'),
            ('A32', 'A32 - COMPUTABLE PAYMENTS FOR ITBIS PERCEIVED'),

            # AVI
            ('A34', 'A34 - TECHNICAL DIRECTION (Art. 4 Norm 07-07)'),
            ('A35', 'A35 - ADMINISTRATION CONTRACT (Art. 4 Paragraph I, Norm 07-07)'),
            ('A36', 'A36 - CONSULTING / FEES'),

            # AVII
            ('A39', 'A39 - SALES OF GOODS ON COMMISSION'),
            ('A40', 'A40 - SALES OF SERVICES IN THE NAME OF THIRD PARTIES'),

            # IX
            ('A45c', 'A45c - OPERATIONS OF PRODUCERS OF EXEMPT GOODS OR SERVICES (local purchase)'),
            ('A45s', 'A45s - OPERATIONS OF PRODUCERS OF EXEMPT GOODS OR SERVICES (Services)'),
            ('A45i', 'A45i - OPERATIONS OF PRODUCERS OF EXEMPT GOODS OR SERVICES (Imports)'),
            ('A46c', 'A46c - TO INCLUDE IN ASSETS (CATEGORY I) (local purchase)'),
            ('A46s', 'A46s - TO INCLUDE IN ASSETS (CATEGORY I) (Services)'),
            ('A46i', 'A46i - TO INCLUDE IN ASSETS (CATEGORY I) (Imports)'),
            ('A47c', 'A47c - OTHER NON-DEDUCTIBLE VAT PAID (local purchase)'),
            ('A47s', 'A47s - OTHER NON-DEDUCTIBLE VAT PAID (Services)'),
            ('A47i', 'A47i - OTHER NON-DEDUCTIBLE VAT PAID (Imports)'),
            ('A49c', 'A49c - IN THE PRODUCTION AND/OR SALE OF EXPORTED GOODS (local purchase)'),
            ('A49s', 'A49s - IN THE PRODUCTION AND/OR SALE OF EXPORTED GOODS (Services)'),
            ('A49i', 'A49i - IN THE PRODUCTION AND/OR SALE OF EXPORTED GOODS (Imports)'),
            ('A50c', 'A50c - IN THE PRODUCTION AND/OR SALE OF TAXABLE GOODS (local purchase)'),
            ('A50s', 'A50s - IN THE PRODUCTION AND/OR SALE OF TAXABLE GOODS (Services)'),
            ('A50i', 'A50i - IN THE PRODUCTION AND/OR SALE OF TAXABLE GOODS (Imports)'),
            ('A51c', 'A51c - IN THE PROVISION OF TAXABLE SERVICE (local purchase)'),
            ('A51s', 'A51s - IN THE PROVISION OF TAXABLE SERVICE (Services)'),
            ('A51i', 'A51i - IN THE PROVISION OF TAXABLE SERVICE (Imports)'),
            ('A53', 'A53 - ITBIS SUBJECT TO PROPORTIONALITY (Imports)'),
        ],
        required=False,
    )
    box_it1 = fields.Selection(
        string='IT-1',
        selection=[
            # IT1II-A
            ('I2', 'I2 - INCOME FROM EXPORTS OF GOODS (Article 342 CT)'),
            ('I3', 'I3 - INCOME FROM SERVICE EXPORTS (Article 344 CT and Article 14, Paragraph j), Regulation 293-11)'),
            ('I4', 'I4 - INCOME FROM LOCAL SALES OF EXEMPT GOODS OR SERVICES (Article 343 and Article 344 CT)'),
            ('I5', 'I5 - INCOME FROM THE SALES OF EXEMPT GOODS OR SERVICES BY DESTINATION'),
            ('I8', 'I8 - INCOME FROM LOCAL SALES OF EXEMPT GOODS (Paragraphs III and IV, Article 343 CT)'),

            # IT1II-B
            ('I15', 'I15 - TAXABLE OPERATIONS FROM SALES OF DEPRECIABLE ASSETS (Categories 2 and 3)'),

            # IT1III
            ('I28', 'I28 - AUTHORIZED COMPENSABLE BALANCES (Other Taxes) AND/OR REFUNDS'),
            ('I31', 'I31 - OTHER COMPUTABLE PAYMENTS TO ACCOUNT'),
            ('I32', 'I32 - AUTHORIZED COMPENSATIONS AND/OR REFUNDS'),

            # IT1IV
            ('I35', 'I35 - SURCHARGES'),
            ('I36', 'I36 - COMPENSATION INTEREST'),
            ('I37', 'I37 - SANCTIONS'),

            # IT1A
            ('I39', 'I39 - SERVICES SUBJECT TO WITHHOLDING INDIVIDUALS'),
            ('I40', 'I40 - SERVICES SUBJECT TO WITHHOLDING NON-PROFIT ENTITIES (Rule No. 01-11)'),
            ('I42', 'I42 - SERVICES SUBJECT TO COMPANY WITHHOLDING (Rule No. 07-09)'),
            ('I43', 'I43 - SERVICES SUBJECT TO COMPANY WITHHOLDING (Rule No. 02-05 AND 07-07)'),
            ('I44', 'I44 - GOODS OR SERVICES SUBJECT TO WITHHOLDING TO TAXPAYERS UNDER THE RST (Rule No. 01-11) '
                    '(Operations Taxed at 18%)'),
            ('I45', 'I45 - GOODS OR SERVICES SUBJECT TO WITHHOLDING TO TAXPAYERS UNDER THE RST (Rule No. 01-11) '
                    '(Operations Taxed at 16%)'),
            ('I47', 'I47 - ASSETS SUBJECT TO RETENTION OF PROOF OF PURCHASE (Operations Taxed at 18%) '
                    '(Rule No. 08-10 and 05-19)'),
            ('I48', 'I48 - ASSETS SUBJECT TO RETENTION OF PROOF OF PURCHASE (Operations Taxed at 16%) '
                    '(Rule No. 08-10 and 05-19)'),
            ('I59', 'I59 - TOTAL ITBIS RECEIVED FOR SALE'),
            ('I61', 'I61 - COMPUTABLE PAYMENTS ON ACCOUNT'),

            # IT1B
            ('I64', 'I64 - SURCHARGES'),
            ('I65', 'I65 - COMPENSATION INTEREST'),
            ('I66', 'I66 - SANCTIONS'),
        ],
        required=False,
    )

