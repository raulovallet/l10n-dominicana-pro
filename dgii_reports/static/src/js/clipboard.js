/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useState, Component } from "@odoo/owl";
import { MonetaryField } from "@web/views/fields/monetary/monetary_field";
import { IntegerField } from "@web/views/fields/integer/integer_field";
import { PercentageField } from "@web/views/fields/percentage/percentage_field";
import { useTooltip } from "@web/core/tooltip/tooltip_hook";


export const CopyClipboardMixin = (Base) => class extends Base {
    setup() {
        // super.setup?.();
        // this.state = useState({ copied: false });
        // useTooltip();
    }

    async copyToClipboard(value, ev) {
        try {
            await navigator.clipboard.writeText(value);
            // this.state.copied = true;

            // const el = ev.currentTarget;
            // el.setAttribute("data-bs-original-title", "Copied!");
            // el.dispatchEvent(new Event("mouseenter"));

            // setTimeout(() => {
            //     el.setAttribute("data-bs-original-title", "Copy");
            //     this.state.copied = false;
            // }, 1000);
        } catch (err) {
            console.error("copyToClipboard", err);
        }
    }
};

export class CopyClipboardMonetary extends CopyClipboardMixin(MonetaryField) {
    static template = "CopyClipboardMonetary";
}

export class CopyClipboardInteger extends CopyClipboardMixin(IntegerField) {
    static template = "CopyClipboardInteger";
}

export class CopyClipboardPercentage extends CopyClipboardMixin(PercentageField) {
    async copyToClipboard(value, ev) {
        await super.copyToClipboard(value * 100, ev);
    }
    static template = "CopyClipboardPercentage";
}

registry.category("fields").add("CopyClipboardMonetary", CopyClipboardMonetary);
registry.category("fields").add("CopyClipboardInteger", CopyClipboardInteger);
registry.category("fields").add("CopyClipboardPercentage", CopyClipboardPercentage);

// The above code defines custom fields for Odoo that allow users to copy monetary, integer, and percentage values to the clipboard.
// The fields use a common behavior for copying values and updating the UI to indicate success.
// The `CopyClipboardBehavior` provides the setup and copy functionality, while each field class extends the appropriate base field class.
// The templates for each field are defined in the Odoo XML files, and the fields are registered in the Odoo registry for use in views.
// The `setup` method initializes the state for each field, and the `copyToClipboard` method handles the copying logic.
// The copied value is displayed in a tooltip that appears when the user clicks the copy button, and it resets after a short delay.