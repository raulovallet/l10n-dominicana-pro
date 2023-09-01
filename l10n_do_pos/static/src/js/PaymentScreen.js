odoo.define('l10n_do_pos.PaymentScreen', function (require) {
    "use strict";


    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    var _t = core._t;


    const L10nDoPosPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            /**
             * @override
             */
            async validateOrder(isForceValidate) {

                var current_order = this.env.pos.get_order();
                var client = current_order.get_partner();
                var total = current_order.get_total_with_tax();
                var fiscal_type = current_order.get_fiscal_type();

                if (total === 0) {
                    this.showPopup('ErrorPopup', {
                        title: _t('Sale in'),
                        body: _t('You cannot make sales in 0, please add a product with value'),
                    });
                    return false;
                }
    
    
                if (this.env.pos.config.l10n_do_fiscal_journal) {
    
                    if (!await this.analyze_payment_methods()) {
                        return false;
                    }

                    if (!current_order.fiscal_type){
                            
                        this.showPopup('ErrorPopup', {
                            title: _t('Required fiscal type'),
                            body: _t('Please select a fiscal type'),
                        });

                        return false;
                    }
    
                    if (current_order.fiscal_type.requires_document && !client) {
    
                        this.showPopup('ErrorPopup', {
                            title: _t('Required document (RNC/Cedula)'),
                            body: _.str.sprintf(
                                _t('For invoice fiscal type %s its necessary customer, please select customer'), fiscal_type.name)
                        });

                        return false;
    
                    }
                    if (fiscal_type.requires_document && !client.vat) {
                        this.showPopup('ErrorPopup', {
                            title: _t('Required document (RNC/Cedula)'),
                            body: _.str.sprintf(
                                _t('For invoice fiscal type %s it is necessary for the customer have RNC or Cedula'), fiscal_type.name)
                        });

                        return false;
                    }
                    
                    if (fiscal_type.requires_document && !(client.vat.length === 9 || client.vat.length === 11)) {
                        this.showPopup('ErrorPopup', {
                            title: _t('Incorrect document (RNC/Cedula)'),
                            body: _.str.sprintf(
                                _t('For invoice fiscal type %s it is necessary for the customer have correct RNC or Cedula without dashes or spaces'), fiscal_type.name)
                        });
                        return false;
                    }

                    if (total >= 250000.00 && (!client || !client.vat)) {
                        this.showPopup('ErrorPopup', {
                            title: _t('Sale greater than RD$ 250,000.00'),
                            body: _t('For this sale it is necessary for the customer have ID'),
                        });
                        return false;
                    }

                    if (current_order.get_fiscal_type().prefix === 'B14'){
                        var has_taxes = false;

                        current_order.get_orderlines().forEach(function (orderline) {
                            orderline.get_applicable_taxes().forEach(function (tax) {
                                var line_tax = orderline._map_tax_fiscal_position(tax);
                                if (line_tax &&
                                    ((line_tax.tax_group_id[1] === 'ITBIS' && line_tax.amount !== 0) || line_tax.tax_group_id[1] === 'ISC')){
                                    has_taxes = true
                                }
                            });
                        });

                        if(has_taxes){
                            this.showPopup('ErrorPopup', {
                                title: _.str.sprintf(_t('Error with Fiscal Type %s'), fiscal_type.name),
                                body: _.str.sprintf(
                                    _t('You cannot pay order of Fiscal Type %s with ITBIS/ISC. Please select correct fiscal position for remove ITBIS and ISC'), fiscal_type.name)
                            });
                            return false;
                        }
                    }
    
                }

                await super.validateOrder(...arguments);
            }

            async _finalizeValidation() {

                var current_order = this.env.pos.get_order();
                if (this.env.pos.config.l10n_do_fiscal_journal && !current_order.to_invoice && !current_order.ncf) {

                    try {

                        var fiscal_data = await this.env.pos.get_fiscal_data(current_order);
                        
                        console.log('NCF Generated', fiscal_data);
                        current_order.ncf = fiscal_data.ncf;
                        current_order.fiscal_type_id = current_order.fiscal_type.id;
                        current_order.ncf_expiration_date = fiscal_data.ncf_expiration_date;
                        current_order.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;

                    } catch (error) {

                        throw error;
                    } 

                    this.env.pos.set_order(current_order);
                    await super._finalizeValidation();

                } else {

                    await super._finalizeValidation();

                }

            }
            /**
             * @override
             */
            async addNewPaymentLine({ detail: paymentMethod }) {
                if(this.env.pos.config.l10n_do_fiscal_journal && paymentMethod && paymentMethod.is_credit_note){
                    
                    const { confirmed, payload: ncf } = await this.showPopup('TextInputPopup', {
                        startingValue: '',
                        title: this.env._t('Please enter the NCF'),
                        placeholder: this.env._t('NCF'),
                    });
                    
                    if(!confirmed || !ncf)  return;
                    
                    const payment_lines = this.currentOrder.get_paymentlines();
                    
                    for (let line of payment_lines) {
                        if (line.payment_method.is_credit_note && line.credit_note_ncf === ncf) {
                            this.showPopup('ErrorPopup', {
                                title: _t('Error'),
                                body: _t('The credit note has already been used in this order'),
                            });
                            return false;
                        }
                    }

                    try {

                        var credit_note = await this.env.pos.get_credit_note(ncf);
                        var credit_note_partner = this.env.pos.db.get_partner_by_id(credit_note.partner_id)

                    } catch (error) {

                        throw error;
                    } 

                    if(credit_note.residual_amount <= 0){
                        this.showPopup('ErrorPopup', {
                            title: _t('Error'),
                            body: _t('The credit note has no residual amount'),
                        });
                        return false;
                    }

                    const current_partner = this.currentOrder.get_partner();

                    if((!current_partner && this.env.pos.config.pos_partner_id && credit_note.partner_id != this.env.pos.config.pos_partner_id[0]) ||
                        (current_partner && credit_note.partner_id != current_partner.id)){
                        this.showPopup('ErrorPopup', {
                            title: _t('Error'),
                            body: _t('The customer of the credit note is not the same as the current order, please select the correct customer.'),
                        });
                        return false;
                    }

                    const amount_due_before_payment = this.currentOrder.get_due()
                    var newPaymentline = this.currentOrder.add_paymentline(paymentMethod);
                    
                    if(newPaymentline){
                        
                        newPaymentline.set_fiscal_data(ncf, credit_note.partner_id);
                        
                        if (!current_partner){
                            this.currentOrder.set_partner(credit_note_partner);
                        }

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

            }
            _updateSelectedPaymentline(){
                if (this.selectedPaymentLine && 
                    this.selectedPaymentLine.payment_method.is_credit_note && 
                    this.env.pos.config.l10n_do_fiscal_journal){
                    this.showPopup('ErrorPopup', {
                        title: _t('Error'), 
                        body: _t('You cannot edit a credit note payment line'),
                    });
                    return;
                }
                super._updateSelectedPaymentline();
            }

            async analyze_payment_methods() {

                var current_order = this.env.pos.get_order();
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

                    if (payment_line.payment_method.is_credit_note && !current_order._isRefundAndSaleOrder()) {

                        if (!payment_line.credit_note_ncf) {
                            this.showPopup('ErrorPopup', {
                                title: _t('Error in credit note'),
                                body: _t('There is an error with the payment of ' +
                                    'credit note, please delete the payment of the ' +
                                    'credit note and enter it again.'),
                            });

                            return false;
                        }

                        
                        try {

                            var credit_note = await this.env.pos.get_credit_note(payment_line.credit_note_ncf);
    
                        } catch (error) {
    
                            throw error;
                        } 

                        if (credit_note.residual_amount <= 0) {
                            this.showPopup('ErrorPopup', {
                                title: _t('Error in credit note'),
                                body: _t('The credit note has no residual amount, please delete the payment of the credit note and enter it again.'),
                            });
                        }

                        if (credit_note.residual_amount < payment_line.amount) {
                            this.showPopup('ErrorPopup', {
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

                    this.showPopup('ErrorPopup', {
                        title: _t('Card payment'),
                        body: _t('Card payments cannot exceed the total order'),
                    });

                    return false;
                }

                if (Math.round(Math.abs(total_in_bank) * 100) / 100 ===
                    Math.round(Math.abs(total) * 100) / 100 && has_cash) {

                    this.showPopup('ErrorPopup', {
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

        };


    Registries.Component.extend(PaymentScreen, L10nDoPosPaymentScreen);
    

    // var screens = require('point_of_sale.screens');
    // var rpc = require('web.rpc');
    // var screens_return = require('pos_orders_history_return.screens');
    // var core = require('web.core');
    // var _t = core._t;

    // screens.ActionpadWidget.include({
    //     renderElement: function () {
    //         this._super();
    //         var current_order = this.pos.get_order();
    //         if (current_order) {
    //             if (current_order.get_mode() === 'return' &&
    //                 this.pos.invoice_journal.l10n_do_fiscal_journal) {
    //                 this.$('.set-customer').addClass('disable');
    //             } else {
    //                 this.$('.set-customer').removeClass('disable');
    //             }
    //         }
    //     },
    // });

    // screens.OrdersHistoryButton.include({
    //     button_click: function () {
    //         if (this.pos.invoice_journal.l10n_do_fiscal_journal &&
    //             !this.pos.config.load_barcode_order_only) {

    //             this.showPopup('ErrorPopup', {
    //                 title: _t('Config'),
    //                 body: _t('Please active Load Specific Orders only it ' +
    //                     'on point of sale config'),
    //             });

    //         } else {
    //             this.pos.db.pos_orders_history = [];
    //             this.pos.db.pos_orders_history_lines = [];
    //             this.pos.db.sorted_orders = [];
    //             this.pos.db.line_by_id = [];
    //             this.pos.db.lines_by_id = [];
    //             this.pos.db.orders_history_by_id = [];
    //             this._super();
    //         }

    //     },
    // });

    // screens.PaymentScreenWidget.include({



    //     renderElement: function () {
    //         this._super();
    //         var self = this;
    //         var current_order = self.pos.get_order();
    //         this.$('.js_set_fiscal_type').click(function () {
    //             self.click_set_fiscal_type();
    //         });
    //         if (current_order) {
    //             if (current_order.get_mode() === 'return' &&
    //                 this.pos.invoice_journal.l10n_do_fiscal_journal) {

    //                 this.$('.js_set_fiscal_type').addClass('disable');
    //                 this.$('.js_set_customer').addClass('disable');
    //                 this.$('.input-button').addClass('disable');
    //                 this.$('.mode-button').addClass('disable');
    //                 this.$('.paymentmethod').addClass('disable');

    //             } else {

    //                 this.$('.js_set_fiscal_type').removeClass('disable');
    //                 this.$('.js_set_customer').removeClass('disable');
    //                 this.$('.input-button').removeClass('disable');
    //                 this.$('.mode-button').removeClass('disable');
    //                 this.$('.paymentmethod').removeClass('disable');

    //             }
    //             if (this.pos.invoice_journal.l10n_do_fiscal_journal) {

    //                 this.$('.js_invoice').hide();

    //             }
    //         }

    //     },





    //     click_paymentmethods: function (id) {
    //         var self = this;
    //         var cashregister = null;
    //         var current_order = self.pos.get_order();

    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal_id[0] === id) {
    //                 cashregister = this.pos.cashregisters[i];
    //                 break;
    //             }
    //         }

    //         if (payment_method.is_for_credit_notes &&
    //             self.pos.config.l10n_do_fiscal_journal) {
    //             this.keyboard_on();
    //             self.gui.show_popup('textinput', {
    //                 title: _t("Enter credit note number"),
    //                 confirm: function (input) {
    //                     current_order.add_payment_credit_note(
    //                         input,
    //                         cashregister
    //                     );
    //                     self.keyboard_off();
    //                 },
    //                 cancel: function () {
    //                     self.keyboard_off();
    //                 },
    //             });
    //         } else {
    //             this._super(id);
    //         }
    //     },
    // });

    // screens_return.OrdersHistoryScreenWidget.include({
    //     load_order_by_barcode: function (barcode) {
    //         var self = this;
    //         var _super = this._super.bind(this);
    //         if (self.pos.config.return_orders &&
    //             self.pos.config.l10n_do_fiscal_journal) {
    //             var order_custom = false;
    //             var domain = [
    //                 ['ncf', '=', barcode],
    //                 ['returned_order', '=', false],
    //             ];
    //             var fields = [
    //                 'pos_history_ref_uid',
    //             ];
    //             self.pos.loading_screen_on();
    //             rpc.query({
    //                 model: 'pos.order',
    //                 method: 'search_read',
    //                 args: [domain, fields],
    //                 limit: 1,
    //             }, {
    //                 timeout: 3000,
    //                 shadow: true,
    //             }).then(function (order) {
    //                 order_custom = order;
    //                 self.pos.loading_screen_off();
    //             }, function (err, ev) {
    //                 self.pos.loading_screen_off();
    //                 console.log(err);
    //                 console.log(ev);
    //                 ev.preventDefault();
    //                 var error_body =
    //                     _t('Your Internet connection is probably down.');
    //                 if (err.data) {
    //                     var except = err.data;
    //                     error_body = except.arguments ||
    //                         except.message || error_body;
    //                 }
    //                 self.gui.show_popup('error', {
    //                     title: _t('Error: Could not Save Changes'),
    //                     body: error_body,
    //                 });
    //             }).done(function () {
    //                 self.pos.loading_screen_off();
    //                 if (order_custom && order_custom.length) {
    //                     _super(order_custom[0].pos_history_ref_uid);
    //                 } else {
    //                     self.gui.show_popup('error', {
    //                         title: _t('Error: Could not find the Order'),
    //                         body: _t('There is no order with this barcode.'),
    //                     });
    //                 }
    //             });
    //         } else {
    //             this._super(barcode);
    //         }
    //     },
    // });
});
