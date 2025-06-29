odoo.define('l10n_do_pos.chrome', function (require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');

    const L10nDoPosChrome = (Chrome) =>
        class extends Chrome {
            /**
             * @override
             * `FloorScreen` is the start screen if there are floors.
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
