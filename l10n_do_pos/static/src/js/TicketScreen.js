odoo.define('l10n_do_pos.TicketScreen', function (require) {
    'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');

    const L10nDoPosTicketScreen = TicketScreen => class extends TicketScreen {
        async _onDoRefund() {
            if (this.env.pos.config.l10n_do_fiscal_journal){
                const {confirmed} = await this.showPopup('ConfirmPopup', {
                    'title': this.env._t('Credit Note'),
                    'body': this.env._t('Are you sure you want to create this credit note?'),
                });
                if (confirmed) {
                    super._onDoRefund();
                    const order = this.getSelectedSyncedOrder();
                    var new_order = this.env.pos.get_order();
                    console.log('order', order);
                    console.log('new_order', new_order);
                    console.log('this', this);
                }
            }
        }
        close() {
            if (this.env.pos.config.l10n_do_fiscal_journal){
                const order = this.getSelectedSyncedOrder();
                var new_order = this.env.pos.get_order();
                console.log('order', order);
                console.log('new_order', new_order);
                console.log('this', this);

            } else {
                super.close();
            }
            

        }

    }

    Registries.Component.extend(TicketScreen, L10nDoPosTicketScreen);
});