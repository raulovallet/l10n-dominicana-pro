odoo.define('l10n_do_pos.PaymentScreen', function (require) {
    "use strict";


    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var Registries = require('point_of_sale.Registries');
    var core = require('web.core');
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
    
                    // if (!this.analyze_payment_methods()) {
                    //     return false;
                    // }
    
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
    
                    // This part is for credit note
                    // if (current_order.get_mode() === 'return') {
                    //     var origin_order = this.pos.db.orders_history_by_id[current_order.return_lines[0].order_id[0]];

                    //     if(origin_order === undefined){
                    //         this.showPopup('ErrorPopup', {
                    //             title: _t('Credit note error'),
                    //             body: _t('Please create credit note again'),
                    //         });
                    //     }
    
                    //     if (origin_order.amount_total < Math.abs(total)) {
                    //         this.showPopup('ErrorPopup', {
                    //             title: _t('The amount of the credit is very high'),
                    //             body: _t('Total amount of the credit note cannot be greater than original'),
                    //         });
                    //         return false;
                    //     }
    
                    //     if (origin_order.partner_id[0] !== client.id) {
                    //         this.showPopup('ErrorPopup', {
                    //             title: _t('Credit note error'),
                    //             body: _t('The customer of the credit note must' +
                    //                 ' be the same as the original'),
                    //         });
                    //         return false;
                    //     }
                    // }
    
                }
                await super.validateOrder(...arguments);
            }

            async _finalizeValidation() {

                var current_order = this.env.pos.get_order();
                console.log(this.env.pos.config.l10n_do_fiscal_journal, current_order)
                if (this.env.pos.config.l10n_do_fiscal_journal && !current_order.to_invoice && !current_order.ncf) {

                    try {
                        console.log('fiscal try')

                        fiscal_data = await this.env.services.rpc({
                            model: 'pos.order',
                            method: 'get_next_fiscal_sequence',
                            args: [
                                false,
                                current_order.fiscal_type.id,
                                this.env.pos.company.id,
                                'no mode',
                                current_order.export_as_JSON().lines,
                                current_order.uid,
                                payments,
                            ],
                        })

                        console.log('fiscal data', fiscal_data)
                        
                        if (fiscal_data){
                            current_order.ncf = fiscal_data.ncf;
                            current_order.fiscal_type_id = current_order.fiscal_type.id;
                            current_order.ncf_expiration_date = fiscal_data.ncf_expiration_date;
                            current_order.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;

                        }else{
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Error: no internet connection.'),
                                body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                            });
                        }

                        // For credit notes
                        // if (current_order.get_mode() === 'return') {
                        //     var origin_order =
                        //         this.env.pos.db.orders_history_by_id[
                        //             current_order.return_lines[0].order_id[0]];
                        //     current_order.ncf_origin_out = origin_order.ncf;
                        // }
                        this.env.pos.set_order(current_order);
                        console.log('NCF Generated', res);

                    } catch (error) {
                        console.log(err);
                        console.log(ev);
                        console.log('fiscal catch')
                        
                        // var error_body = _t('Your Internet connection is probably down.');
                        
                        // if (err.data) {
                        //     var except = err.data;
                        //     error_body = except.arguments ||
                        //         except.message || error_body;
                        // }

                        // this.showPopup('ErrorPopup', {
                        //     title: _t('Error: Could not Save Changes'),
                        //     body: error_body,
                        // });

                        throw error;

                    } finally {
                        console.log('fiscal finally')
                        await super._finalizeValidation();

                    }

                    // var payments = [];
                    // current_order.get_paymentlines().forEach(function (item) {
                    //     return payments.push(item.export_as_JSON());
                    // });

                } else {
                    await super._finalizeValidation();
                }

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

    //     keyboard_off: function () {
    //         // That one comes from BarcodeEvents
    //         $(body:).keypress(this.keyboard_handler);
    //         // That one comes from the pos, but we prefer to cover
    //         // all the basis
    //         $(body:).keydown(this.keyboard_keydown_handler);
    //     },
    //     keyboard_on: function () {
    //         $(body:).off('keypress', this.keyboard_handler);
    //         $(body:).off('keydown', this.keyboard_keydown_handler);
    //     },

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

    //     open_vat_popup: function () {
    //         var self = this;
    //         var current_order = self.pos.get_order();
    //         self.keyboard_on();
    //         self.gui.show_popup('textinput', {
    //             title: _t('You need to select a customer with RNC/Céd for' +
    //                 ' this fiscal type, place writes RNC/Céd'),
    //             'vat': '',
    //             confirm: function (vat) {
    //                 self.keyboard_off();
    //                 if (!(vat.length === 9 || vat.length === 11) ||
    //                     Number.isNaN(Number(vat))) {

    //                     self.gui.show_popup('error', {
    //                         title: _t('This not RNC or Cédula'),
    //                         body: _t('Please check if RNC or Cédula is' +
    //                             ' correct'),
    //                         cancel: function () {
    //                             self.open_vat_popup();
    //                         },
    //                     });

    //                 } else {
    //                     // TODO: in future try optimize search partners
    //                     // link get_partner_by_id
    //                     self.keyboard_off();
    //                     var partner = self.pos.partners.find(
    //                         function (partner_obj) {
    //                             return partner_obj.vat === vat;
    //                         }
    //                     );
    //                     if (partner) {
    //                         current_order.set_client(partner);
    //                     } else {
    //                         // TODO: in future create automatic partner
    //                         self.gui.show_screen('clientlist');
    //                     }
    //                 }

    //             },
    //             cancel: function () {
    //                 self.keyboard_off();
    //                 if (!current_order.get_client()) {
    //                     current_order.set_fiscal_type(
    //                         this.pos.get_fiscal_type_by_prefix('B02')
    //                     );
    //                 }
    //             },
    //         });
    //     },

    //     click_set_fiscal_type: function () {
    //         var self = this;
    //         var fiscal_type_list = _.map(self.pos.fiscal_types,
    //             function (fiscal_type) {
    //                 if (fiscal_type.type === 'out_invoice') {
    //                     return {
    //                         label: fiscal_type.name,
    //                         item: fiscal_type,
    //                     };
    //                 }
    //                 return false;
    //             });

    //         self.gui.show_popup('selection', {
    //             title: _t('Select Fiscal Type'),
    //             list: fiscal_type_list,
    //             confirm: function (fiscal_type) {
    //                 var current_order = self.pos.get_order();
    //                 var client = self.pos.get_client();
    //                 current_order.set_fiscal_type(fiscal_type);
    //                 if (fiscal_type.requires_document && !client) {
    //                     self.open_vat_popup();
    //                 }
    //                 if (fiscal_type.requires_document && client) {
    //                     if (!client.vat ) {
    //                         self.open_vat_popup();
    //                     }
    //                 }
    //             },
    //             is_selected: function (fiscal_type) {
    //                 return fiscal_type === self.pos.get_order().fiscal_type;
    //             },
    //         });
    //     },

    //     analyze_payment_methods: function () {

    //         var current_order = this.pos.get_order();
    //         var total_in_bank = 0;
    //         var has_cash = false;
    //         var all_payment_lines = current_order.get_paymentlines();
    //         var total = current_order.get_total_with_tax();
    //         var has_return_ncf = true;
    //         var payment_and_return_mount_equals = true;


    //         for (var line in all_payment_lines) {
    //             var payment_line = all_payment_lines[line];

    //             if (payment_line.cashregister.journal.type === 'bank') {
    //                 total_in_bank = +Number(payment_line.amount);
    //             }
    //             if (payment_line.cashregister.journal.type === 'cash') {
    //                 has_cash = true;
    //             }
    //             if (payment_line.cashregister.journal.is_for_credit_notes) {

    //                 if (payment_line.get_returned_ncf() === null) {
    //                     has_return_ncf = false;
    //                 }

    //                 var amount_in_payment_line =
    //                     Math.round(payment_line.amount * 100) / 100;
    //                 var amount_in_return_order =
    //                     Math.abs(
    //                         payment_line.get_returned_order_amount() * 100
    //                     ) / 100;

    //                 if (amount_in_return_order !== amount_in_payment_line) {
    //                     payment_and_return_mount_equals = false;
    //                 }
    //             }
    //         }

    //         if (Math.abs(Math.round(Math.abs(total) * 100) / 100) <
    //             Math.round(Math.abs(total_in_bank) * 100) / 100) {

    //             this.showPopup('ErrorPopup', {
    //                 title: _t('Card payment'),
    //                 body: _t('Card payments cannot exceed the total order'),
    //             });

    //             return false;
    //         }

    //         if (Math.round(Math.abs(total_in_bank) * 100) / 100 ===
    //             Math.round(Math.abs(total) * 100) / 100 && has_cash) {

    //             this.showPopup('ErrorPopup', {
    //                 title: _t('Card and cash payment'),
    //                 body: _t('The total payment with the card is ' +
    //                     'sufficient to pay the order, please eliminate the ' +
    //                     'payment in cash or reduce the amount to be paid by ' +
    //                     'card'),
    //             });

    //             return false;
    //         }

    //         if (!has_return_ncf) {

    //             this.showPopup('ErrorPopup', {
    //                 title: _t('Error in credit note'),
    //                 body: _t('There is an error with the payment of ' +
    //                     'credit note, please delete the payment of the ' +
    //                     'credit note and enter it again.'),
    //             });

    //             return false;

    //         }

    //         if (!payment_and_return_mount_equals) {

    //             this.showPopup('ErrorPopup', {
    //                 title: _t('Error in credit note'),
    //                 body: _t('The amount of the credit note does not ' +
    //                     'correspond, delete the credit note and enter it' +
    //                     ' again.'),
    //             });

    //             return false;
    //         }

    //         return true;


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

    //         if (cashregister.journal.is_for_credit_notes &&
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
