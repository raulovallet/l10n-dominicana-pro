import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order.
         This method may be overridden to implement custom invoice generation
         (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        #import ipdb; ipdb.set_trace()  # noqa
        
        partner_id = self.partner_id
        partner_fiscal_type_id = partner_id.sale_fiscal_type_id

        if not partner_fiscal_type_id:
            prefix = 'B01' if partner_id.vat else 'B02'
            fiscal_type = self.env[
                'account.fiscal.type'].search([
                    ('type', '=', 'out_invoice'),
                    ('prefix', '=', prefix),
                ], limit=1)
            if not fiscal_type:
                raise ValidationError(
                    _("There's not a fiscal type for prefix {}, please create "
                      "it.").format(prefix))
            invoice_vals['fiscal_type_id'] = fiscal_type.id

        elif partner_id.parent_id and partner_id.parent_id.is_company \
                and partner_id.parent_id.sale_fiscal_type_id:
            invoice_vals['fiscal_type_id'] = \
                partner_id.parent_id.sale_fiscal_type_id.id

        else:
            invoice_vals['fiscal_type_id'] = partner_fiscal_type_id.id

        return invoice_vals

    def _finalize_invoices(self, invoices, references):
        """
        Invoked after creating invoices at the end of action_invoice_create.
        :param invoices: {group_key: invoice}
        :param references: {invoice: order}
        """
        for invoice in invoices.values():
            if invoice.journal_id.l10n_do_fiscal_journal:
                invoice.write({
                    'reference': False
                })
        super(SaleOrder, self)._finalize_invoices(invoices, references)