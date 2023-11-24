odoo.define('l10n_do_pos.PartnerListScreen', function (require) {
    'use strict';

    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
    const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const { isConnectionError } = require('point_of_sale.utils');
    const { useListener } = require("@web/core/utils/hooks");
    const { useAsyncLockedMethod } = require("point_of_sale.custom_hooks");

    const L10nDoPosPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {

            async saveChanges(event) {

                try {
                    let partnerId = await this.rpc({
                        model: 'res.partner',
                        method: 'create_from_ui',
                        args: [event.detail.processedChanges],
                    });
                    
                    await this.env.pos.load_new_partners();
                    
                    var new_partner = this.env.pos.db.get_partner_by_id(partnerId);
                    this.editPartner(new_partner);
                    
                    var $partner_name = $('.partner-name');
                    var $vat = $('.vat');

                    $partner_name.val(new_partner.name);
                    $vat.val(new_partner.vat);

                    this.state.selectedPartner = new_partner;
                    this.props.partner = new_partner;
                    
                } catch (error) {
                    if (isConnectionError(error)) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Unable to save changes.'),
                        });
                    } else {
                        throw error;
                    }
                }
            }
        };

    const L10nDoPosPartnerDetailsEdit = (PartnerDetailsEdit) => class extends PartnerDetailsEdit {
        saveChanges() {

            var $partner_name = $('.partner-name')
            var $vat = $('.vat')

            if ($partner_name && $partner_name.val() != this.changes.name){
                this.changes.name = $partner_name.val()
            }

            if ($vat && $vat.val() != this.changes.vat){
                this.changes.vat = $vat.val()
            }

            super.saveChanges();
        }
    };

    Registries.Component.extend(PartnerListScreen, L10nDoPosPartnerListScreen);
    Registries.Component.extend(PartnerDetailsEdit, L10nDoPosPartnerDetailsEdit);

    return PartnerListScreen;
});
