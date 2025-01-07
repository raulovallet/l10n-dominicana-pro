# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    def _get_res_partner_list(self):
        
        POS_CONSUMER_PARTNER = self.env.ref('l10n_do_pos.default_pos_partner')
        DEFAULT_PARTNER = self.env.ref('l10n_do_pos.default_pos_partner')
        
        
        return {
            'pos_consumer_partner': POS_CONSUMER_PARTNER.id,
            'default_pos_partner': DEFAULT_PARTNER.id
        }

    def unlink(self):
        if self.filtered(lambda x: x.id in self._get_res_partner_list().values()):
            raise UserError(_("You can't delete this partner."))
        return super(ResPartner, self).unlink()