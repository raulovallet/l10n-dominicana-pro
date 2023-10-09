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
                if (fiscalPos.type !== 'out_invoice') continue;
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
                var partner = this.currentOrder.get_partner();

                if (selectedFiscalType.requires_document && (!partner || !partner.vat))
                    await this.open_vat_popup();
                
                this.currentOrder.set_fiscal_type(selectedFiscalType);
            }
        }

        async open_vat_popup() {
            var self = this;

            const { confirmed, payload: vat } = await this.showPopup('TextInputPopup', {
                startingValue: '',
                title: this.env._t('You need to select a customer with RNC or Cedula for this fiscal type.'),
                placeholder: this.env._t('RNC or Cedula'),
            });

            if (confirmed) {
                if (!(vat.length === 9 || vat.length === 11) || Number.isNaN(Number(vat))) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('This not RNC or Cedula'),
                        body: this.env._t('Please ensure the RNC has exactly 9 digits or the Cedula has 11 digits'),
                        cancel: function () {
                            self.open_vat_popup();
                        },
                    });

                } else {
                    // TODO: in future try optimize search partners
                    // link get_partner_by_id
                    var partner = this.env.pos.partners.find(
                        function (partner_obj) {
                            return partner_obj.vat === vat;
                        }
                    );
                    if (partner) {

                        this.currentOrder.set_partner(partner);

                    } else {
                        // TODO: in future create automatic partner
                        const { confirmed, payload: newPartner } = await this.showTempScreen(
                            'PartnerListScreen',
                            { partner: this.currentOrder.get_partner()}
                        );
                        if (confirmed) {
                            this.currentOrder.set_partner(newPartner);
                            this.currentOrder.updatePricelist(newPartner);
                        }
                    }
                } 
            }
        }
    }

    SetFiscalTypeButton.template = 'SetFiscalTypeButton';
    Registries.Component.add(SetFiscalTypeButton);

    return SetFiscalTypeButton;
});