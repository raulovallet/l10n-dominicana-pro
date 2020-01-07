# © 2018 Manuel Marquez <buzondemam@gmail.com>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        """This method is being overwritten as Odoo uses the purchase reference
            and puts it into the invoice reference (our NCF), we change this
            behaviour to use the invoice name (description)"""
        # TODO create tests
        result = super(AccountInvoice, self).purchase_order_change()

        vendor_ref = self.purchase_id.partner_ref
        if vendor_ref:
            # Here, l10n_dominicana changes self.reference to self.name
            self.name = ", ".join([self.name, vendor_ref]) if (
                self.name and vendor_ref not in self.name) else vendor_ref

        return result