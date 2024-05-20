/** @odoo-module **/
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";
import { useInputField } from "@web/views/fields/input_field_hook";
import { _t } from "@web/core/l10n/translation";



export class UrlField extends Component {
    static template = "web.UrlField";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
        text: { type: String, optional: true },
        websitePath: { type: Boolean, optional: true },
    };

    setup() {
        useInputField({ getValue: () => this.props.record.data[this.props.name] || "" });
    }

    get formattedHref() {
        let value = this.props.record.data[this.props.name];
        if (value && !this.props.websitePath) {
            const regex = /^((ftp|http)s?:\/)?\//i; // http(s)://... ftp(s)://... /...
            value = !regex.test(value) ? `dgii_reports/${value}` : value;
        }
        return value;
    }
}

export const urlField = {
    component: UrlField,
    displayName: _t("URL"),
    supportedOptions: [
        {
            label: _t("Is a website path"),
            name: "website_path",
            type: "boolean",
            help: _t("If True, the url will be used as it is, without any prefix added to it."),
        },
    ],
    supportedTypes: ["char"],
    extractProps: ({ attrs, options }) => ({
        text: attrs.text,
        websitePath: options.website_path,
        placeholder: attrs.placeholder,
    }),
};



registry.category("fields").add("dgii_reports_url", urlField);