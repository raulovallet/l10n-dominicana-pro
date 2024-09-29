/** @odoo-module */

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();
        console.log('this OrderReceipt', this)
        console.log('order', this.env.services.pos.get_order())
    },
    isSimple(line) {
        if (this.env.services.pos.config.l10n_do_fiscal_journal){
            return false;
        }
        return super.isSimple(line);
    }
})
