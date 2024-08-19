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

    sale_fiscal_type_id = fields.Many2one(
        comodel_name="account.fiscal.type",
        string="Sale Fiscal Type",
        domain=[("type", "=", "out_invoice")],
        compute='_compute_sale_fiscal_type_id',
        inverse='_inverse_sale_fiscal_type_id',
        index=True,
        store=True,
    )
    purchase_fiscal_type_id = fields.Many2one(
        comodel_name="account.fiscal.type",
        string="Purchase Fiscal Type",
        domain=[("type", "=", "in_invoice")],
    )
    expense_type = fields.Selection(
        selection=[
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

    @api.depends('sale_fiscal_type_id')
    def _compute_is_fiscal_info_required(self):
        for rec in self:
            rec.is_fiscal_info_required = rec.sale_fiscal_type_id.prefix in ['B01', 'B14', 'B15']

    def _get_fiscal_type_domain(self, prefix):
        return self.env['account.fiscal.type'].search([
            ('type', '=', 'out_invoice'),
            ('prefix', '=', prefix),
        ], limit=1)

    @api.depends('vat', 'country_id', 'name')
    def _compute_sale_fiscal_type_id(self):
        for partner in self.sudo():
            vat = partner.name if partner.name and isinstance(partner.name,
                                                              str) and partner.name.isdigit() else partner.vat
            is_dominican_partner = partner.country_id == self.env.ref('base.do')

            new_fiscal_type = self._determine_fiscal_type(partner, vat, is_dominican_partner)

            partner.sale_fiscal_type_id = new_fiscal_type
            partner.sudo().set_fiscal_position_from_fiscal_type(new_fiscal_type)

    def _determine_fiscal_type(self, partner, vat, is_dominican_partner):
        if not is_dominican_partner:
            return self._get_fiscal_type_domain('B16')

        if partner.parent_id:
            return partner.parent_id.sale_fiscal_type_id

        if vat and isinstance(vat, str) and not partner.sale_fiscal_type_id:
            return self._determine_fiscal_type_by_vat(partner, vat)

        if is_dominican_partner and not partner.sale_fiscal_type_id:
            return self._get_fiscal_type_domain('B02')

        return partner.sale_fiscal_type_id

    def _determine_fiscal_type_by_vat(self, partner, vat):
        if vat.isdigit() and len(vat) == 9:
            if 'MINISTERIO' in (partner.name or '').upper():
                return self._get_fiscal_type_domain('B15')
            if any(keyword in (partner.name or '').upper() for keyword in ('IGLESIA', 'ZONA FRANCA')):
                return self._get_fiscal_type_domain('B14')
            return self._get_fiscal_type_domain('B01')
        return self._get_fiscal_type_domain('B02')

    def _inverse_sale_fiscal_type_id(self):
        for partner in self:
            partner.sale_fiscal_type_id = partner.sale_fiscal_type_id
            self.sudo().set_fiscal_position_from_fiscal_type(partner.sale_fiscal_type_id)

    @api.model
    def get_sale_fiscal_type_id_selection(self):
        return {
            "sale_fiscal_type_id": self.sale_fiscal_type_id.id,
            "sale_fiscal_type_list": self.sale_fiscal_type_list,
            "sale_fiscal_type_vat": self.sale_fiscal_type_vat
        }

    def set_fiscal_position_from_fiscal_type(self, fiscal_type):
        if fiscal_type:
            for company in self.env['res.company'].sudo().search([]):
                company_new_fiscal_type = fiscal_type.with_company(company).sudo()

                if company_new_fiscal_type.fiscal_position_id:
                    self.with_company(company).sudo().write({
                        'property_account_position_id': company_new_fiscal_type.fiscal_position_id.id
                    })

    sale_fiscal_type_list = [
        {"id": "final", "name": "Consumo", "ticket_label": "Consumo", "is_default": True},
        {"id": "fiscal", "name": "Crédito Fiscal"},
        {"id": "gov", "name": "Gubernamental"},
        {"id": "special", "name": "Regímenes Especiales"},
        {"id": "unico", "name": "Único Ingreso"},
        {"id": "export", "name": "Exportaciones"}
    ]

    sale_fiscal_type_vat = {
        "rnc": ["fiscal", "gov", "special"],
        "ced": ["final", "fiscal"],
        "other": ["final"],
        "no_vat": ["final", "unico", "export"]
    }
