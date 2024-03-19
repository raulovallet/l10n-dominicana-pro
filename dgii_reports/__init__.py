# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>

from . import controllers
from . import models
from . import wizard


from odoo import api, SUPERUSER_ID

def update_taxes(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tax_template_ids = env['ir.model.data'].search([
        ('model', '=', 'account.tax.template'),
        ('module', '=', 'l10n_do'),
    ])
    for tax_template_id in tax_template_ids:
        tax_ids = env['ir.model.data'].search([
            ('model', '=', 'account.tax'),
            ('module', '=', 'l10n_do'),
            ('name', 'like', '%_' + tax_template_id.name), 
        ])
        
        taxes = env['account.tax'].browse(tax_ids.mapped('res_id')) if tax_ids else False
        
        if taxes:
            tax_template_obj = env['account.tax.template'].browse(tax_template_id.res_id)
            taxes.write({
                'l10n_do_tax_type': tax_template_obj.l10n_do_tax_type,
                'isr_retention_type': tax_template_obj.isr_retention_type,
                'tax_group_id': tax_template_obj.tax_group_id.id
            })
