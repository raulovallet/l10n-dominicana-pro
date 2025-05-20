/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CopyClipboardNumberField extends Component {
    setup() {
        this.copyText = this.env._t("Copy");
        this.successText = this.env._t("Copied");
    }
    
    async copyToClipboard() {
        try {
            const text = this.props.value?.toString() || "";
            await navigator.clipboard.writeText(text);

            this.copyText = this.successText;
            this.render();

            setTimeout(() => {
                this.copyText = this.env._t("Copy");
                this.render();
            }, 1000);
        } catch (error) {
            console.error("Clipboard copy failed:", error);
            this.copyText = this.env._t("Error");
            this.render();
        }
    }
}
CopyClipboardNumberField.template = "dgii_reports.CopyClipboardNumberField";
CopyClipboardNumberField.props = {
    ...standardFieldProps,
};

registry.category("fields").add("CopyClipboardNumber", CopyClipboardNumberField);
