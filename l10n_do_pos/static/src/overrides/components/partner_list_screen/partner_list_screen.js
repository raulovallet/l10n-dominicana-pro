/** @odoo-module */

import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerListScreen.prototype, {
    async saveChanges(processedChanges) {
        //new logic
        const partnerId = await this.orm.call("res.partner", "create_from_ui", [processedChanges]);
        await this.pos._loadPartners([partnerId]);
        var new_partner = this.pos.db.get_partner_by_id(partnerId);
        this.editPartner(new_partner);
        var $partner_name = $('.partner-name');
        var $vat = $('.vat');
        $partner_name.val(new_partner.name);
        $vat.val(new_partner.vat);
        this.state.selectedPartner = new_partner
        this.confirm();
    }
})

