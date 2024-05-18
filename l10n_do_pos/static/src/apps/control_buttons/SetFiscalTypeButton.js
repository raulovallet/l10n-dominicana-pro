/** @odoo-module */

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";



export class SetFiscalTypeButton extends Component {
    static template = 'l10n_do_pos.SetFiscalTypeButton';
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }

    get currentOrder() {
        return this.pos.get_order();
    }

    get currentFiscalTypeName() {
        return this.currentOrder && this.currentOrder.fiscal_type
            ? this.currentOrder.fiscal_type.name
            : _t('Select Fiscal Type');
    }

    async onClick() {
        const currentFiscalType = this.currentOrder.fiscal_type;
        const fiscalPosList = [];
        for (let fiscalPos of this.pos.fiscal_types) {
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

        const { confirmed, payload: selectedFiscalType } = await this.popup.add(
            SelectionPopup,
            {
                title: _t("Select Fiscal Type"),
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

        //nuevo popup
        const { confirmed, payload: vat } = await this.popup.add(
            TextInputPopup,
            {
                startingValue: '',
                title: _t('You need to select a customer with RNC or Cedula for this fiscal type.'),
                placeholder: _t('RNC or Cedula'),
            }
        );

        //nuevo confirmed
        if (confirmed) {
            if (!(vat.length === 9 || vat.length === 11) || Number.isNaN(Number(vat))) {

                this.popup.add(ErrorPopup, {
                    title: _t('This not RNC or Cedula'),
                    body: _t('Please ensure the RNC has exactly 9 digits or the Cedula has 11 digits'),
                    cancel: function () {
                        self.open_vat_popup();
                    },
                });

            } else {
                // TODO: in future try optimize search partners like get_partner_by_id

                var partner = this.pos.db.get_partners_sorted().find(partner_obj => partner_obj.vat === vat);

                if (partner) {

                    this.currentOrder.set_partner(partner);

                } else {
                    // TODO: in future create automatic partner
                    const { confirmed, payload: newPartner } = await this.pos.showTempScreen("PartnerListScreen", {
                        partner: this.currentOrder.get_partner()
                    });

                    if (confirmed) {
                        this.currentOrder.set_partner(newPartner);
                        this.currentOrder.updatePricelist(newPartner);
                    }
                }
            }
        }
    }
}
