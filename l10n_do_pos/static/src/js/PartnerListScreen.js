odoo.define('l10n_do_pos.PartnerListScreen', function (require) {
    'use strict';

    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
    const Registries = require('point_of_sale.Registries');
    const { isConnectionError } = require('point_of_sale.utils');

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
                    this.state.selectedPartner = this.env.pos.db.get_partner_by_id(partnerId);
                    this.props.resolve({ confirmed: true, payload: this.state.selectedPartner });
                    this.editPartner(this.state.selectedPartner);
                    var $partner_name = $('.partner-name')
                    var $vat = $('.vat')
                    $partner_name.val(this.state.selectedPartner.name)
                    $vat.val(this.state.selectedPartner.vat)
                    
                    console.log('this', this)
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

    Registries.Component.extend(PartnerListScreen, L10nDoPosPartnerListScreen);

    return PartnerListScreen;
});
