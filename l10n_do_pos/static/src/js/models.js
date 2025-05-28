odoo.define('l10n_do_pos.models', function (require) {
    "use strict";
    
    var field_utils = require('web.field_utils');
    const { Gui } = require('point_of_sale.Gui');
    var core = require('web.core');
    var { Order, PosGlobalState, Payment, Orderline} = require('point_of_sale.models');
    var Registries = require('point_of_sale.Registries');
    var _t = core._t;

    const L10nDoPosPosGlobalState = PosGlobalState => class extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.fiscal_types = loadedData['account.fiscal.type']
        }

        get_fiscal_type_by_id(id) {
            var self = this;
            var res_fiscal_type = false;
            self.fiscal_types.forEach(function (fiscal_type) {
                if (fiscal_type.id === id) {
                    res_fiscal_type = fiscal_type;
                }
            });

            if (!res_fiscal_type) {
                res_fiscal_type = this.get_fiscal_type_by_prefix('B02');
            }

            return res_fiscal_type;
        }

        get_fiscal_type_by_prefix(prefix) {
            var self = this;
            var res_fiscal_type = false;
            
            // TODO: try make at best performance
            self.fiscal_types.forEach(function (fiscal_type) {
                if (fiscal_type.prefix === prefix) {
                    res_fiscal_type = fiscal_type;
                }
            });

            if (res_fiscal_type)
                return res_fiscal_type;
    
            Gui.showPopup('ErrorPopup', {
                'title': _t('Fiscal type not found'),
                'body': _.str.sprintf(_t('This fiscal type not exist. (%s)'), prefix),
            });

            return false;
        }        
        async get_fiscal_data(order) {
            return this.env.services.rpc({
                model: 'pos.order',
                method: 'get_next_fiscal_sequence',
                args: [
                    false,
                    order.fiscal_type.id,
                    this.env.pos.company.id,
                    [],
                    order.export_as_JSON()
                ],
            });
        }
        isCreditNoteMode() {
            const current_order = this.env.pos.get_order();
            return this.env.pos.config.l10n_do_fiscal_journal && current_order && current_order._isRefundAndSaleOrder();
        }
        get_credit_note_payment_method() {
            var credit_note_payment_method = false;
            
            this.env.pos.payment_methods.forEach(
                function (payment_method) {
                    if (payment_method.is_credit_note) {
                        credit_note_payment_method = payment_method;
                    }
                }
            );

            return credit_note_payment_method;
        }
        async get_credit_note(ncf) {
            return this.env.services.rpc({
                model: 'pos.order',
                method: 'get_credit_note',
                args: [
                    false,
                    ncf
                ],
            });
        }
        async get_credit_notes(partner_id) {
            return this.env.services.rpc({
                model: 'pos.order',
                method: 'get_credit_notes',
                args: [
                    false,
                    partner_id
                ],
            });
        }

    }

    const L10nDoPosOrder = Order => class extends Order {
        /**
         * @override
         */
        constructor(obj, options) {
            super(...arguments); 

            if (this.pos.config.l10n_do_fiscal_journal){

                this.ncf = this.ncf || '';
                this.ncf_origin_out = this.ncf_origin_out || '';
                this.ncf_expiration_date = this.ncf_expiration_date = '';
                this.fiscal_type_id = this.fiscal_type || false;
                this.fiscal_sequence_id = this.fiscal_sequence_id || false;

                var partner = this.get_partner();

                if (partner && partner.sale_fiscal_type_id) {
    
                    this.set_fiscal_type(this.pos.get_fiscal_type_by_id(partner.sale_fiscal_type_id[0]));
    
                } else {
    
                    this.set_fiscal_type(this.pos.get_fiscal_type_by_prefix('B02'))
    
                }    
            }
            
        }

        set_fiscal_type(fiscal_type) {
            this.fiscal_type = fiscal_type;
            this.fiscal_type_id = fiscal_type.id;

            if (fiscal_type && fiscal_type.fiscal_position_id){
                this.set_fiscal_position(_.find(this.pos.fiscal_positions, function(fp) {
                    return fp.id === fiscal_type.fiscal_position_id[0];
                }));
                for (let line of this.get_orderlines()) {
                    line.set_quantity(line.quantity);
                }
            }
        }

        get_fiscal_type() {
            return this.fiscal_type;
        }

        set_partner(partner){

            super.set_partner(partner); 

            if (partner && partner.sale_fiscal_type_id) { 
                this.set_fiscal_type(this.pos.get_fiscal_type_by_id(partner.sale_fiscal_type_id[0]));
            } else {
                this.set_fiscal_type(this.pos.get_fiscal_type_by_prefix('B02'));
            }
        }
        
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            if(this.pos.config.l10n_do_fiscal_journal){
                json.ncf = this.ncf;
                json.ncf_origin_out = this.ncf_origin_out;
                json.ncf_expiration_date = this.ncf_expiration_date;
                json.fiscal_type_id = this.fiscal_type_id;
                json.fiscal_sequence_id = this.fiscal_sequence_id;
            }
            return json;
        }

        init_from_JSON(json) {
            super.init_from_JSON(...arguments);

            if (this.pos.config.l10n_do_fiscal_journal){

                this.ncf = json.ncf || '';
                this.ncf_origin_out = json.ncf_origin_out || '';
                this.ncf_expiration_date = json.ncf_expiration_date || '';
                this.fiscal_type_id = json.fiscal_type_id || false;
                this.fiscal_sequence_id = json.fiscal_sequence_id || false;

                if(json.fiscal_type_id)
                    this.set_fiscal_type(this.pos.get_fiscal_type_by_id(json.fiscal_type_id));

                if(json.fiscal_type)
                    this.set_fiscal_type(json.fiscal_type);

            }
        }

        export_for_printing() {
            var result = super.export_for_printing(...arguments);
            result.l10n_do_fiscal_journal = this.pos.config.l10n_do_fiscal_journal;

            if(this.pos.config.l10n_do_fiscal_journal){
                result.ncf = this.ncf;
                result.ncf_origin_out = this.ncf_origin_out;
                result.ncf_expiration_date = this.ncf_expiration_date ? 
                    field_utils.format.date(field_utils.parse.date(this.ncf_expiration_date, {}, {isUTC: true})): '';
                result.fiscal_type = this.fiscal_type;
            }

            return result;
        }
        
        set_ncf_origin_out(origin_order) {
            this.ncf_origin_out = origin_order.ncf;
        }
        
        set_l10n_do_fiscal_data(fiscal_data){
            this.ncf = fiscal_data.ncf;
            this.ncf_expiration_date = fiscal_data.ncf_expiration_date;
            this.fiscal_sequence_id = fiscal_data.fiscal_sequence_id;
        }

    }
    
    const L10nDoPayment = Payment => class extends Payment {
        /**
         * @override
         */
        constructor(obj, options) {
            super(...arguments); 

            this.credit_note_ncf = this.credit_note_ncf || '';
            this.credit_note_partner_id = this.credit_note_partner_id || false;
        }
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.credit_note_ncf = this.credit_note_ncf;
            json.credit_note_partner_id = this.credit_note_partner_id;
            return json;
        }
        //@override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.credit_note_ncf = json.credit_note_ncf;
            this.credit_note_partner_id = json.credit_note_partner_id;
        }
        set_fiscal_data(ncf, partner_id){
            this.credit_note_ncf = ncf;
            this.credit_note_partner_id = partner_id;
        }
    }

    const L10nDoPosOrderLine = Orderline => class extends Orderline {
        export_for_printing (){
            let res = super.export_for_printing();
            res.l10n_do_itbis = this.get_itbis();

            return res;
        }

        get_itbis() {
            let itbis = 0;
            const tax_details = this.get_tax_details();
            
            for (const tax_id in tax_details) {
                if (this.pos.taxes_by_id[tax_id].tax_group_id[1] === 'ITBIS') {
                    itbis += tax_details[tax_id].amount;
                }
            }

            return itbis;
        }
    }

    Registries.Model.extend(PosGlobalState, L10nDoPosPosGlobalState);
    Registries.Model.extend(Order, L10nDoPosOrder);
    Registries.Model.extend(Orderline, L10nDoPosOrderLine);
    Registries.Model.extend(Payment, L10nDoPayment);

});
