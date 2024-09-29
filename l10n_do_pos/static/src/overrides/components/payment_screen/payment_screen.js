/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { SetFiscalTypeButton } from "@l10n_do_pos/apps/control_buttons/SetFiscalTypeButton";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

PaymentScreen.components['SetFiscalTypeButton'] =   SetFiscalTypeButton
patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        var current_order = this.pos.get_order();
        var client = current_order.get_partner();
        var total = current_order.get_total_with_tax();
        var fiscal_type = current_order.get_fiscal_type();

        if (total === 0) {
            this.popup.add(ErrorPopup, {
                title: _t('Sale in'),
                body: _t('You cannot make sales in 0, please add a product with value'),
            });

            return false;
        }


        if (this.pos.config.l10n_do_fiscal_journal) {

            if (!await this.analyze_payment_methods()) {
                return false;
            }
            if (!current_order.fiscal_type){
                this.popup.add(ErrorPopup, {
                    title: _t('Required fiscal type'),
                    body: _t('Please select a fiscal type'),
                });
                return false;
            }

            if (current_order.fiscal_type.requires_document && !client) {
                this.popup.add(ErrorPopup, {
                    title: _t('Required document (RNC/Cedula)'),
                    body: _.str.sprintf(
                        _t('For invoice fiscal type %s its necessary customer, please select customer'), fiscal_type.name)
                });

                return false;

            }
            if (fiscal_type.requires_document && !client.vat) {
                this.popup.add(ErrorPopup, {
                    title: _t('Required document (RNC/Cedula)'),
                    body: _.str.sprintf(
                        _t('For invoice fiscal type %s it is necessary for the customer have RNC or Cedula'), fiscal_type.name)
                });
                return false;
            }

            if (fiscal_type.requires_document && !(client.vat.length === 9 || client.vat.length === 11)) {

                this.popup.add(ErrorPopup, {
                    title: _t('Incorrect document (RNC/Cedula)'),
                    body: _.str.sprintf(
                        _t('For invoice fiscal type %s it is necessary for the customer have correct RNC or Cedula without dashes or spaces'), fiscal_type.name)
                });
                return false;
            }

            if (total >= 250000.00 && (!client || !client.vat)) {
                this.popup.add(ErrorPopup, {
                    title: _t('Sale greater than RD$ 250,000.00'),
                    body: _t('For this sale it is necessary for the customer have ID'),
                });
                return false;
            }

            if (current_order.get_fiscal_type().prefix === 'B14'){
                var has_taxes = false;

                current_order.get_orderlines().forEach(function (orderline) {
                    orderline._getProductTaxesAfterFiscalPosition().forEach(function (tax) {
                        if ((tax.tax_group_id[1] === 'ITBIS' && tax.amount !== 0) || tax.tax_group_id[1] === 'ISC'){
                            has_taxes = true
                        }
                    });
                });
                if(has_taxes){
                    this.popup.add(ErrorPopup, {
                        title: _.str.sprintf(_t('Error with Fiscal Type %s'), fiscal_type.name),
                        body: _.str.sprintf(
                            _t('You cannot pay order of Fiscal Type %s with ITBIS/ISC. Please select correct fiscal position for remove ITBIS and ISC'), fiscal_type.name)
                    });

                    return false;
                }
            }

        }

        await super.validateOrder(...arguments);
    },

    //aqui esta el error de xml
    async _finalizeValidation() {

        var current_order = this.currentOrder;
        if (this.pos.config.l10n_do_fiscal_journal && !current_order.to_invoice && !current_order.ncf) {
            try {
                var fiscal_data = await this.pos.get_fiscal_data(current_order);
                console.log('fiscal data', fiscal_data)
                //current_order.ncf = fiscal_data.ncf;
                current_order.fiscal_type_id = current_order.fiscal_type.id;
                current_order.ncf_expiration_date = fiscal_data.ncf_expiration_date;
                current_order.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;
                current_order.set_ncf(fiscal_data.ncf)


            } catch (error) {
                console.log('errrrorrrrr')
                throw error;
            }

            //this.pos.set_order(current_order);
            await super._finalizeValidation();

        } else {

            await super._finalizeValidation();

        }

    },
    /**
     * @override
     */
    async addNewPaymentLine({ detail: paymentMethod }) {
        if(this.pos.config.l10n_do_fiscal_journal && paymentMethod && paymentMethod.is_credit_note){
            const current_partner = this.currentOrder.get_partner();

            if (current_partner && current_partner.id !== this.pos.config.pos_partner_id[0]) {
                try {
                    const credit_notes = await this.pos.get_credit_notes(current_partner.id);

                    const { confirmed: confirmedPickingCreditNote, payload: credit_note } = await this.popup.add(
                        SelectionPopup,
                        {
                            title: this.env._t('Select Credit Note'),
                            list: credit_notes,
                        }
                    );

                    if (!confirmedPickingCreditNote || !credit_note) return;

                } catch (error) {

                    throw error;
                }

            }else{

                const { confirmed, payload: ncf } = await this.popup.add(
                    TextInputPopup,
                    {
                        startingValue: '',
                        title: this.env._t('Please enter the NCF'),
                        placeholder: this.env._t('NCF'),
                    }
                );


                if(!confirmed || !ncf)  return;

                try {

                    var credit_note = await this.pos.get_credit_note(ncf);

                } catch (error) {

                    throw error;
                }
            }

            var credit_note_partner = this.pos.db.get_partner_by_id(credit_note.partner_id)
            const payment_lines = this.currentOrder.get_paymentlines();

            for (let line of payment_lines) {
                if (line.payment_method.is_credit_note && line.credit_note_ncf === credit_note.ncf) {
                    this.popup.add(ErrorPopup, {
                        title: _t('Error'),
                        body: _t('The credit note has already been used in this order'),
                    });

                    return false;
                }
            }

            if(credit_note.residual_amount <= 0){
                this.popup.add(ErrorPopup, {
                    title: _t('Error'),
                    body: _.str.sprintf(_t('Credit note %s has no available amount.'), credit_note.ncf)
                });

                return false;
            }

            if (!credit_note_partner) {

                this.popup.add(ErrorPopup, {
                    title: _t('Error'),
                    body: _t('The customer of the credit note is not the same as the current order, please select the correct customer.'),
                });

                return false;
            }

            const amount_due_before_payment = this.currentOrder.get_due()
            var newPaymentline = this.currentOrder.add_paymentline(paymentMethod);

            if(newPaymentline){

                if (!current_partner){
                    this.currentOrder.set_partner(credit_note_partner);
                }

                newPaymentline.set_fiscal_data(credit_note.ncf, credit_note.partner_id);

                if(credit_note.residual_amount < amount_due_before_payment){
                    newPaymentline.set_amount(credit_note.residual_amount);
                }

                NumberBuffer.reset();

                return true;

            } else {

                return false;

            }

        }


        return super.addNewPaymentLine(...arguments);

    },
    _updateSelectedPaymentline(){
        if (this.selectedPaymentLine &&
            this.selectedPaymentLine.payment_method.is_credit_note &&
            this.pos.config.l10n_do_fiscal_journal){
            this.popup.add(ErrorPopup, {
                title: _t('Error'),
                body: _t('You cannot edit a credit note payment line'),
            });
            return;
        }
        super._updateSelectedPaymentline();
    },

    async analyze_payment_methods() {

        var current_order = this.pos.get_order();
        var total_in_bank = 0;
        var has_cash = false;
        var payment_lines = current_order.get_paymentlines();
        var total = current_order.get_total_with_tax();
        var has_return_ncf = true;
        // var payment_and_return_mount_equals = true;


        for (let payment_line of payment_lines) {
            if (payment_line.payment_method.type === 'bank') {
                total_in_bank = +Number(payment_line.amount);
            }

            if (payment_line.payment_method.type === 'cash') {
                has_cash = true;
            }

            if (payment_line.payment_method.is_credit_note && !current_order._isRefundOrder()) {
                if (!payment_line.credit_note_ncf) {
                    this.popup.add(ErrorPopup, {
                        title: _t('Error in credit note'),
                        body: _t('There is an error with the payment of ' +
                            'credit note, please delete the payment of the ' +
                            'credit note and enter it again.'),
                    });
                    return false;
                }
                try {
                    var credit_note = await this.pos.get_credit_note(payment_line.credit_note_ncf);

                } catch (error) {

                    throw error;
                }

                if (credit_note.residual_amount <= 0) {
                    this.popup.add(ErrorPopup, {
                        title: _t('Error in credit note'),
                        body: _t('The credit note has no residual amount, please delete the payment of the credit note and enter it again.'),
                    });
                }
                if (credit_note.residual_amount < payment_line.amount) {
                    this.popup.add(ErrorPopup, {
                        title: _t('Error in credit note'),
                        body: _t(
                            'The amount of the credit note is less than the amount entered, please delete the payment of the credit note and enter it again.'),
                    });
                }

                // TODO: Check if this is necessary
                // var amount_in_payment_line =
                //     Math.round(payment_line.amount * 100) / 100;
                // var amount_in_return_order =
                //     Math.abs(
                //         payment_line.get_returned_order_amount() * 100
                //     ) / 100;

                // if (amount_in_return_order !== amount_in_payment_line) {
                //     payment_and_return_mount_equals = false;
                // }
            }
        }

        if (Math.abs(Math.round(Math.abs(total) * 100) / 100) <
            Math.round(Math.abs(total_in_bank) * 100) / 100) {
            this.popup.add(ErrorPopup, {
                title: _t('Card payment'),
                body: _t('Card payments cannot exceed the total order'),
            });

            return false;
        }

        if (Math.round(Math.abs(total_in_bank) * 100) / 100 ===
            Math.round(Math.abs(total) * 100) / 100 && has_cash) {
            this.popup.add(ErrorPopup, {
                title: _t('Card and cash payment'),
                body: _t('The total payment with the card is ' +
                    'sufficient to pay the order, please eliminate the ' +
                    'payment in cash or reduce the amount to be paid by ' +
                    'card'),
            });

            return false;
        }


        // TODO: Check if this is necessary
        // if (!payment_and_return_mount_equals) {

        //     this.showPopup('ErrorPopup', {
        //         title: _t('Error in credit note'),
        //         body: _t('The amount of the credit note does not ' +
        //             'correspond, delete the credit note and enter it' +
        //             ' again.'),
        //     });

        //     return false;
        // }

        return true;

    }
})
