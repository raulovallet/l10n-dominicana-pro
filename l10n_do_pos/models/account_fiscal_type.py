# -*- coding: utf-8 -*-

from odoo import models, _, api
from odoo.exceptions import ValidationError

class AccountFiscalType(models.Model):
    _inherit = 'account.fiscal.type'
    
    def get_active_sessions(self):
        self.ensure_one()
        return self.env['pos.session'].search([
            ('state', '!=', 'closed'),
        ])

    def get_pos_config_names(self, pos_sessions):
        self.ensure_one()
        pos_configs = pos_sessions.mapped('config_id')
        return ', '.join(pos_configs.mapped('name'))

    def write(self, vals):
        if 'active' in vals and vals['active'] is False:
            for fiscal_type in self:
                pos_sessions = fiscal_type.get_active_sessions()
                if pos_sessions:
                    config_names = fiscal_type.get_pos_config_names(pos_sessions)
                    raise ValidationError(_('You cannot archive a fiscal type'))
        return super(AccountFiscalType, self).write(vals)