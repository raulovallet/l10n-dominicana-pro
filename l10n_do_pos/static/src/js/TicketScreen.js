odoo.define('l10n_do_pos.TicketScreen', function (require) {
    'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    const L10nDoPosTicketScreen = TicketScreen => class extends TicketScreen {
        setup() {
            super.setup();
            useListener('refund-all-order', this._returnAllOrder);
        }

        async _onDoRefund() {
            const order = this.getSelectedSyncedOrder();

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

            const allToRefundDetails = this._getRefundableDetails(partner);
            if (allToRefundDetails.length == 0) {
                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
                return;
            }

            if (this.env.pos.config.l10n_do_fiscal_journal){
                const refund_fiscal_type = this.env.pos.get_fiscal_type_by_prefix('B04');
                const credit_note_payment_method = this.env.pos.get_credit_note_payment_method();

                if (!credit_note_payment_method) {
                    await this.showPopup('ErrorPopup', {
                        'title': this.env._t('Error'),
                        'body': this.env._t('There are no credit note payment method configured.'),
                    });
                    return;
                } 

                if(!refund_fiscal_type){
                    await this.showPopup('ErrorPopup', {
                        'title': this.env._t('Error'),
                        'body': this.env._t('The fiscal type credit note does not exist. Please activate or configure it.'),
                    });
                    return;
                }

                if (order.ncf == '') {
                    await this.showPopup('ErrorPopup', {
                        'title': this.env._t('Error'),
                        'body': this.env._t('This order has no NCF'),
                    });
                    return;
                }
                
            }
            //TODO: check updatePricelist

            await super._onDoRefund();

        }
        async _onCloseScreen() {
            var new_order = this.env.pos.get_order();
            const order = this.getSelectedSyncedOrder();
            if (new_order && this.env.pos.config.l10n_do_fiscal_journal && new_order._isRefundAndSaleOrder() && order.ncf){
                
                try {
                    const refund_fiscal_type = this.env.pos.get_fiscal_type_by_prefix('B04');
                    const credit_note_payment_method = this.env.pos.get_credit_note_payment_method();
                    new_order.set_ncf_origin_out(order.ncf);
                    new_order.set_fiscal_type(refund_fiscal_type);
                    // Convert the date string to a Date object
                    const orderDate = new Date(order.validation_date);
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
                    this.showScreen('PaymentScreen');
                    // TODO: maybe do not need this validation
                    // var fiscal_data = await this.env.pos.get_fiscal_data(new_order);
                    // console.log('NCF Generated', fiscal_data);
                    // new_order.ncf = fiscal_data.ncf;
                    // new_order.fiscal_type_id = new_order.fiscal_type.id;
                    // new_order.ncf_expiration_date = fiscal_data.ncf_expiration_date;
                    // new_order.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;
                    // console.log('GO TO VALIDATE ORDER', this)

                } catch (error) {

                    // TODO: when error show ticket screen
                    this.env.pos.add_new_order();
                    this.env.pos.removeOrder(new_order);
                    throw error;
                } 

            } else {

                super._onCloseScreen();

            }
        }
        _getSearchFields() {
            var fields = super._getSearchFields();
            if (this.env.pos.config.l10n_do_fiscal_journal){
                fields.NCF = {
                    repr: (order) => order.ncf,
                    displayName: this.env._t('NCF'),
                    modelField: 'ncf',
                };
            }
            return fields;
        }
        _prepareRefundOrderlineOptions(orderline) {
            var new_order_line = super._prepareRefundOrderlineOptions(orderline);
            console.log('new_order_line', new_order_line)
            console.log('orderline', orderline)
            console.log('this', this)
            console.log('test', Object.values(this.env.pos.toRefundLines))
            return new_order_line;
        }
        _returnAllOrder(){
            console.log('returnAll')
            const order = this.getSelectedSyncedOrder();
            if (!order) return NumberBuffer.reset();

            for (const orderline of order.orderlines) {
                // Your code here
                const toRefundDetail = this._getToRefundDetail(orderline);
                const refundableQty = toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
                if (refundableQty > 0) {
                    toRefundDetail.qty = refundableQty;
                }

            }
        
        }

    }

    Registries.Component.extend(TicketScreen, L10nDoPosTicketScreen);
});