/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

class CopyClipboardNumberField extends Component {

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.CopyText = "";
        this.value = this.props.record.data[this.props.name]?.toString() || "";
        this.resetOthers = () => {
            this.copyText = _t("Copy");
            this.render();
        };
        document.addEventListener('copy-reset', this.resetOthers);
    }



    getButtonClass() {
        return this.copyText === _t('Copied') ? 'btn btn-success btn-sm' : 'btn btn-outline-secondary btn-sm';
    }
    
    async copyToClipboard() {
        try {
            if (!this.props?.name || !this.props?.record?.data) {
                return;
            }
            
            document.dispatchEvent(new CustomEvent('copy-reset'));

            const text = this.value;
            await navigator.clipboard.writeText(text);

            this.copyText = _t("Copied");
            this.render();

            setTimeout(() => {
                this.copyText = _t("Copy");
                this.render();
            }, 10000);
            
        } catch (error) {
            console.error("Clipboard copy failed:", error);
            this.copyText = _t("Error");
            this.render();
        }
    }

    willUnmount() {
        document.removeEventListener('copy-reset', this.resetOthers);
    }
}

CopyClipboardNumberField.template = "dgii_reports.CopyClipboardNumberField";


export const CopyClipboardNumber = {
    component: CopyClipboardNumberField
};

registry.category("fields").add("CopyClipboardNumber", CopyClipboardNumber);
