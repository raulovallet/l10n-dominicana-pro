/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";

console.log("=== DGII Widget Loading ===");

class DgiiUrlWidget extends Component {
    
    static props = {
        ...standardFieldProps,
    };

    setup() {

    }

    get fieldValue() {
        if (!this.props?.name || !this.props?.record?.data) {
            return "";
        }
        const value = this.props.record.data[this.props.name];
        return value || "";
    }

    get displayText() {
        const text = this.fieldValue || "";
        return text;
    }

    onClick() {
        if (this.fieldValue && this.fieldValue !== "") {
            const url = `dgii_reports/${this.fieldValue}`;
            console.log("Opening URL:", url);
            window.open(url, '_blank');
        }
    }
}

DgiiUrlWidget.template = "dgii_reports.DgiiUrlWidget";

export const UrlWidget = {component: DgiiUrlWidget};

registry.category("fields").add("dgii_reports_url", UrlWidget);