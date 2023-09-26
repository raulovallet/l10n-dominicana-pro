from odoo import models, fields, api, _
import logging
import json
import re
_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(str(err))

    
class Partner(models.Model):
    _inherit = "res.partner"

    ##### delete for migration
    # def _get_l10n_do_dgii_payer_types_selection(self):
    #     """Return the list of payer types needed in invoices to clasify
    #     accordingly to DGII requirements."""
    #     return [
    #         ("taxpayer", "Contribuyente Fiscal"),
    #         ("non_payer", "No Contribuyente"),
    #         ("nonprofit", "Organización sin ánimo de lucro"),
    #         ("special", "Régimen Especial"),
    #         ("governmental", "Gubernamental"),
    #         ("foreigner", "Extranjero/a"),
    #         ("self", "Empresa del sistema"),
    #     ]

    # def _get_l10n_do_expense_type(self):
    #     """Return the list of expenses needed in invoices to clasify accordingly to
    #     DGII requirements."""
    #     return [
    #         ("01", _("01 - Personal")),
    #         ("02", _("02 - Work, Supplies and Services")),
    #         ("03", _("03 - Leasing")),
    #         ("04", _("04 - Fixed Assets")),
    #         ("05", _("05 - Representation")),
    #         ("06", _("06 - Admitted Deductions")),
    #         ("07", _("07 - Financial Expenses")),
    #         ("08", _("08 - Extraordinary Expenses")),
    #         ("09", _("09 - Cost & Expenses part of Sales")),
    #         ("10", _("10 - Assets Acquisitions")),
    #         ("11", _("11 - Insurance Expenses")),
    #     ]
    # def _inverse_l10n_do_dgii_tax_payer_type(self):
    #     for partner in self:
    #         partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type
    
    # @api.depends("vat", "country_id", "name")
    # def _compute_l10n_do_dgii_payer_type(self):
    #     """Compute the type of partner depending on soft decisions"""
    #     company_id = self.env["res.company"].search(
    #         [("id", "=", self.env.user.company_id.id)]
    #     )
    #     for partner in self:
    #         if partner.id == company_id.partner_id.id:
    #             partner.l10n_do_dgii_tax_payer_type = "self"
    #             continue

    #         vat = str(partner.vat if partner.vat else partner.name)
    #         is_dominican_partner = bool(partner.country_id == self.env.ref("base.do"))

    #         if partner.country_id and not is_dominican_partner:
    #             partner.l10n_do_dgii_tax_payer_type = "foreigner"

    #         elif vat and (
    #             not partner.l10n_do_dgii_tax_payer_type
    #             or partner.l10n_do_dgii_tax_payer_type == "non_payer"
    #         ):
    #             if partner.country_id and is_dominican_partner:
    #                 if vat.isdigit() and len(vat) == 9:
    #                     if not partner.vat:
    #                         partner.vat = vat
    #                     if partner.name and "MINISTERIO" in partner.name:
    #                         partner.l10n_do_dgii_tax_payer_type = "governmental"
    #                     elif partner.name and any(
    #                         [n for n in ("IGLESIA", "ZONA FRANCA") if n in partner.name]
    #                     ):
    #                         partner.l10n_do_dgii_tax_payer_type = "special"
    #                     elif vat.startswith("1"):
    #                         partner.l10n_do_dgii_tax_payer_type = "taxpayer"
    #                     elif vat.startswith("4"):
    #                         partner.l10n_do_dgii_tax_payer_type = "nonprofit"
    #                     else:
    #                         partner.l10n_do_dgii_tax_payer_type = "taxpayer"

    #                 elif len(vat) == 11:
    #                     if vat.isdigit():
    #                         if not partner.vat:
    #                             partner.vat = vat
    #                         partner.l10n_do_dgii_tax_payer_type = "taxpayer"
    #                     else:
    #                         partner.l10n_do_dgii_tax_payer_type = "non_payer"
    #                 else:
    #                     partner.l10n_do_dgii_tax_payer_type = "non_payer"
    #         elif not partner.l10n_do_dgii_tax_payer_type:
    #             partner.l10n_do_dgii_tax_payer_type = "non_payer"
    #         else:
    #             partner.l10n_do_dgii_tax_payer_type = (
    #                 partner.l10n_do_dgii_tax_payer_type
    #             )

    # l10n_do_dgii_tax_payer_type = fields.Selection(
    #     selection="_get_l10n_do_dgii_payer_types_selection",
    #     compute="_compute_l10n_do_dgii_payer_type",
    #     string="Taxpayer Type",
    #     index=True,
    #     store=True,
    # )
    # l10n_do_expense_type = fields.Selection(
    #     selection="_get_l10n_do_expense_type",
    #     string="Expense Type",
    #     index=True,
    #     store=True,
    # )
    # def _get_l10n_do_expense_type(self):
    #     """Return the list of expenses needed in invoices to clasify accordingly to
    #     DGII requirements."""
    #     return [
    #         ("01", _("01 - Personal")),
    #         ("02", _("02 - Work, Supplies and Services")),
    #         ("03", _("03 - Leasing")),
    #         ("04", _("04 - Fixed Assets")),
    #         ("05", _("05 - Representation")),
    #         ("06", _("06 - Admitted Deductions")),
    #         ("07", _("07 - Financial Expenses")),
    #         ("08", _("08 - Extraordinary Expenses")),
    #         ("09", _("09 - Cost & Expenses part of Sales")),
    #         ("10", _("10 - Assets Acquisitions")),
    #         ("11", _("11 - Insurance Expenses")),
    #     ]        
    #################

    @api.depends('sale_fiscal_type_id')
    def _compute_is_fiscal_info_required(self):
        for rec in self:
            if rec.sale_fiscal_type_id.prefix in ['B01', 'B14', 'B15']:
                rec.is_fiscal_info_required = True
            else:
                rec.is_fiscal_info_required = False


    sale_fiscal_type_id = fields.Many2one(
        "account.fiscal.type",
        string="Sale Fiscal Type",
        domain=[("type", "=", "out_invoice")],
        compute='_compute_sale_fiscal_type_id',
        inverse='_inverse_sale_fiscal_type_id',
        index=True,
        store=True,
    )

    sale_fiscal_type_list = [{
        "id": "final",
        "name": "Consumo",
        "ticket_label": "Consumo",
        "is_default": True
    }, {
        "id": "fiscal",
        "name": "Crédito Fiscal"
    }, {
        "id": "gov",
        "name": "Gubernamental"
    }, {
        "id": "special",
        "name": "Regímenes Especiales"
    }, {
        "id": "unico",
        "name": "Único Ingreso"
    }, {
        "id": "export",
        "name": "Exportaciones"
    }]

    sale_fiscal_type_vat = {
        "rnc": ["fiscal", "gov", "special"],
        "ced": ["final", "fiscal"],
        "other": ["final"],
        "no_vat": ["final", "unico", "export"]
    }

    purchase_fiscal_type_id = fields.Many2one(
        "account.fiscal.type",
        string="Purchase Fiscal Type",
        domain=[("type", "=", "in_invoice")],
    )
    expense_type = fields.Selection(
        [
            ("01", "01 - Gastos de Personal"),
            ("02", "02 - Gastos por Trabajo, Suministros y Servicios"),
            ("03", "03 - Arrendamientos"),
            ("04", "04 - Gastos de Activos Fijos"),
            ("05", u"05 - Gastos de Representación"),
            ("06", "06 - Otras Deducciones Admitidas"),
            ("07", "07 - Gastos Financieros"),
            ("08", "08 - Gastos Extraordinarios"),
            ("09", "09 - Compras y Gastos que forman parte del Costo de Venta"),
            ("10", "10 - Adquisiciones de Activos"),
            ("11", "11 - Gastos de Seguro"),
        ],
        string="Expense Type",
    )

    is_fiscal_info_required = fields.Boolean(
        compute="_compute_is_fiscal_info_required"
    )

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        ondelete='restrict',
        default=lambda self: self.env.ref('base.do')
    )

    def _get_fiscal_type_domain(self, prefix):
        fiscal_type = self.env[
            'account.fiscal.type'].search([
                ('type', '=', 'out_invoice'),
                ('prefix', '=', prefix),
            ], limit=1)
        
        return fiscal_type

    
    @api.depends('vat', 'country_id', 'name')
    def _compute_sale_fiscal_type_id(self):
        """ Compute the type of partner depending on soft decisions"""

        for partner in self:
            vat = str(partner.vat) if partner.vat else False
            is_dominican_partner = bool(partner.country_id == self.env.ref('base.do'))

            if not is_dominican_partner:
                partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B16')

            elif vat:

                if vat.isdigit() and len(vat) == 9:
                    if partner.name and 'MINISTERIO' in partner.name:
                        partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B15')

                    elif partner.name and any([n for n in ('IGLESIA', 'ZONA FRANCA') if n in partner.name]):
                        partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B14')

                    else:
                        partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B01')

                else:
                    partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B02')

            else:
                partner.sale_fiscal_type_id = partner.sale_fiscal_type_id

    def _inverse_sale_fiscal_type_id(self):
        pass

    @api.model
    def get_sale_fiscal_type_id_selection(self):
        return {
            "sale_fiscal_type_id": self.sale_fiscal_type_id.id,
            "sale_fiscal_type_list": self.sale_fiscal_type_list,
            "sale_fiscal_type_vat": self.sale_fiscal_type_vat
        }