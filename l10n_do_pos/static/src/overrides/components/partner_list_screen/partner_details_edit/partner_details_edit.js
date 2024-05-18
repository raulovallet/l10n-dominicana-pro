/** @odoo-module */

import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";

patch(PartnerDetailsEdit.prototype, {
    saveChanges() {
        var $partner_name = $('.partner-name')
        var $vat = $('.vat')
        if ($partner_name && $partner_name.val() != this.changes.name){
            this.changes.name = $partner_name.val()
        }
        if ($vat && $vat.val() != this.changes.vat){
            this.changes.vat = $vat.val()
        }
        super.saveChanges();
    }
})

