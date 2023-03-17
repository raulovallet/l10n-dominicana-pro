/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
var translation = require('web.translation');
var _t = translation._t;
const { Component, useRef } = owl;


export class FieldDgiiAutoComplete extends Component {
    static template = 'FieldDgiiAutoComplete'
    setup() {
        super.setup();
        this.input = useRef('input_name')
        useInputField({ getValue: () => this.props.value || "", refName: "input_name" });
    }
    _onChangeName(ev) {
        var self = this;
        $(this.input.el).autocomplete({
            source: "/dgii_ws/",
            minLength: 3,
            select: function(event, ui) {

                $(self.input.el).val(ui.item.name);
                var $rnc = $("div[name$='vat']>input");
                $rnc.val(ui.item.rnc).trigger("change");
                $rnc.val(ui.item.rnc).trigger("update");



                return false;
            },
        });
    }
}

registry.category("fields").add("dgii_autocomplete", FieldDgiiAutoComplete);