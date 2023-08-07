odoo.define('l10n_do_pos.SetFiscalTypeButton', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class SetFiscalTypeButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        get currentFiscalTypeName() {
            return this.currentOrder && this.currentOrder.fiscal_type
                ? this.currentOrder.fiscal_type.name
                : this.env._t('Select Fiscal Type');
        }

        async onClick() {
            const currentFiscalType = this.currentOrder.fiscal_type;
            const fiscalPosList = [];
            for (let fiscalPos of this.env.pos.fiscal_types) {
                fiscalPosList.push({
                    id: fiscalPos.id,
                    label: fiscalPos.name,
                    isSelected: currentFiscalType
                        ? fiscalPos.id === currentFiscalType.id
                        : false,
                    item: fiscalPos,
                });
            }
            const { confirmed, payload: selectedFiscalType } = await this.showPopup(
                'SelectionPopup',
                {
                    title: this.env._t('Select Fiscal Type'),
                    list: fiscalPosList,
                }
            );
            if (confirmed) {
                this.currentOrder.set_fiscal_type(selectedFiscalType);
            }
        }
    }

    SetFiscalTypeButton.template = 'SetFiscalTypeButton';
    Registries.Component.add(SetFiscalTypeButton);

    return SetFiscalTypeButton;
});