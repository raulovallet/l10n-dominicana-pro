odoo.define('l10n_do_pos.chrome', function (require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');

    const L10nDoPosChrome = (Chrome) =>
        class extends Chrome {
            /**
             * @override
             * This method overrides the startScreen property to change the
             * initial screen based on the POS state.
             * If the POS is in credit note mode, it will return the PaymentScreen.
             * Otherwise, it will return the default start screen.
             */
            get startScreen() {
                if (this.env.pos.isCreditNoteMode()) {
                    return { name: 'PaymentScreen' };
                } 
                return super.startScreen;
            }

        };

    Registries.Component.extend(Chrome, L10nDoPosChrome);

    return Chrome;
});
