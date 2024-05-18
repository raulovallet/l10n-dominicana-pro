/** @odoo-module */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";


patch(TicketScreen.prototype, {
    async onDoRefund(){
        const order = this.getSelectedOrder();
        if (!order) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return;
        }
        if (this._doesOrderHaveSoleItem(order)) {
            if (!this._prepareAutoRefundOnOrder(order)) {
                // Don't proceed on refund if preparation returned false.
                return;
            }
        }

        const partner = order.get_partner();
        // Lógica adicional para verificar configuraciones específicas del POS
        if (this.pos.config.l10n_do_fiscal_journal){
            const refund_fiscal_type = this.pos.get_fiscal_type_by_prefix('B04');
            const credit_note_payment_method = this.pos.get_credit_note_payment_method();

            if (!credit_note_payment_method) {
                this.popup.add(ErrorPopup, {
                    'title': _t('Error'),
                    'body': _t('There are no credit note payment method configured.'),
                });
                return;
            }

            if(!refund_fiscal_type){
                this.popup.add(ErrorPopup, {
                    'title': _t('Error'),
                    'body': _t('The fiscal type credit note does not exist. Please activate or configure it.'),
                });
                return;
            }

            if (order.ncf == '') {
                this.popup.add(ErrorPopup, {
                    'title': _t('Error'),
                    'body': _t('This order has no NCF'),
                });
                return;
            }
        }

        // Invocar la función original modificada usando super().
        await super.onDoRefund();
    },
    closeTicketScreen(){
        var new_order = this.pos.get_order();
        const order = this.getSelectedOrder();
        if (new_order && this.pos.config.l10n_do_fiscal_journal && new_order._isRefundOrder() && order.ncf){
            try {
                const refund_fiscal_type = this.pos.get_fiscal_type_by_prefix('B04');
                const credit_note_payment_method = this.pos.get_credit_note_payment_method();
                new_order.set_ncf_origin_out(order.ncf);
                new_order.set_fiscal_type(refund_fiscal_type);
                // Convert the date string to a Date object
                const orderDate = new Date(order.date_order);
                // Get the current date
                const currentDate = new Date();
                // Calculate the time difference in milliseconds
                const timeDifferenceMilliseconds = currentDate - orderDate;
                // Calculate the time difference in days
                const timeDifferenceDays = timeDifferenceMilliseconds / (1000 * 60 * 60 * 24);
                // Check if the difference is greater than 30 days and clear the tax_ids if so
                if (timeDifferenceDays > 30) {
                    // Iterate through each orderline in new_order and clear the tax_ids

                    // TODO: only remove ITBIS tax
                    new_order.orderlines.forEach(orderline => {
                        orderline.tax_ids = [];
                    });
                }
                new_order.add_paymentline(credit_note_payment_method);
                //this.showScreen('PaymentScreen');
                this.pos.showScreen("PaymentScreen");

                // TODO: maybe do not need this validation

            } catch (error) {
                // TODO: when error show ticket screen
                this.pos.add_new_order();
                this.pos.removeOrder(new_order);
                throw error;
            }

        }else {
            super.closeTicketScreen();
        }

    },
    _getSearchFields() {
        var fields = super._getSearchFields();
        if (this.pos.config.l10n_do_fiscal_journal){
            fields.NCF = {
                repr: (order) => order.ncf,
                displayName: 'NCF',
                modelField: 'ncf',
            };
        }
        return fields;
    },
})
