from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class PortalAccount(CustomerPortal):
    @http.route(
        ["/my/invoices/<int:invoice_id>"], type="http", auth="public", website=True
    )
    def portal_my_invoice_detail(
        self, invoice_id, access_token=None, report_type=None, download=False, **kw
    ):
        try:
            invoice_sudo = self._document_check_access(
                "account.move", invoice_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        _logger.info(invoice_sudo)

        # Verificamos la localización fiscal del país de la empresa
        fiscal_country_code = invoice_sudo.company_id.account_fiscal_country_id.code
        if (
            report_type in ("html", "pdf", "text")
            and fiscal_country_code == 'DO'  # Código ISO del país de la República Dominicana
        ):
            # return self._show_report(
            #     model=invoice_sudo,
            #     report_type=report_type,
            #     download=download,
            #     report_ref="l10n_do_accounting.l10n_do_account_invoice",
            # )

            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices')

        return super(PortalAccount, self).portal_my_invoice_detail(
            invoice_id, access_token, report_type, download, **kw
        )
