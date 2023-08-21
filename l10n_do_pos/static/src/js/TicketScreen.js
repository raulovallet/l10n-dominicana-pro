odoo.define('l10n_do_pos.TicketScreen', function (require) {
    'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');

    const L10nDoPosTicketScreen = TicketScreen => class extends TicketScreen {
        async _onDoRefund() {
            const order = this.getSelectedSyncedOrder();
            const refund_fiscal_type = this.env.pos.get_fiscal_type_by_prefix('B04');
            const credit_note_payment_method = this.env.pos.get_credit_note_payment_method();

            if (!credit_note_payment_method) {
                await this.showPopup('ErrorPopup', {
                    'title': this.env._t('Error'),
                    'body': this.env._t('There are no credit note payment method configured.'),
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

            if (!order) {
                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
                return;
            }

            if(!refund_fiscal_type){
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
                
                if (order.ncf == '') {
                    await this.showPopup('ErrorPopup', {
                        'title': this.env._t('Error'),
                        'body': this.env._t('This order has no NCF'),
                    });
                    return;
                }
                
                // TODO: maybe do not need this validation
                // const {confirmed} = await this.showPopup('ConfirmPopup', {
                //     'title': this.env._t('Credit Note'),
                //     'body': this.env._t('Are you sure you want to create this credit note?'),
                // });

                // if (!confirmed) 
                //     return;
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
                    new_order.set_ncf_origin_out(order.ncf);
                    new_order.set_fiscal_type(refund_fiscal_type);
                    new_order.add_paymentline(refund_fiscal_type);
                    this.showScreen('PaymentScreen');

                    // T3ODO: maybe do not need this validation
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

    }

    Registries.Component.extend(TicketScreen, L10nDoPosTicketScreen);
});