// /** @odoo-module **/
// import { registry } from "@web/core/registry";
// import { useInputField } from "@web/views/fields/input_field_hook";
// import time from 'web.time';
// var translation = require('web.translation');
// var _t = translation._t;
// const { Component, useRef } = owl;


// export class FieldDgiiAutoComplete extends Component {
//     static template = 'FieldDgiiAutoComplete'
//     setup() {
//         super.setup();
//         this.input = useRef('input_name')
//         useInputField({ getValue: () => this.props.value || "", refName: "input_name" });
//     }
//     _onChangeName(ev) {
//         debugger;
//     }
// }

// registry.category("fields").add("dgii_autocomplete", FieldDgiiAutoComplete);



// export class DomainSelectorTextField extends Component {
//     static template = 'FieldDateMultipleDate'
//     setup() {
//         super.setup();
//         this.input = useRef('inputdate')
//         useInputField({ getValue: () => this.props.value || "", refName: "inputdate" });
//     }
//     _onSelectDateField(ev) {
//         var dateFormat = time.getLangDateFormat();
//         if (dateFormat.includes('MMMM')) {
//             var dates = dateFormat.toLowerCase()
//             var result = dates.replace(/mmmm/g, 'MM');
//             dateFormat = result
//         } else if (dateFormat.includes('MMM')) {
//             var dates = dateFormat.toLowerCase()
//             var result = dates.replace(/mmm/g, 'M');
//             dateFormat = result
//         } else if (dateFormat.includes('ddd')) {
//             var dates = new dateFormat.toLowerCase()
//             var result = new dates.replace(/ddd/g, 'DD');
//             dateFormat = result
//         } else {
//             dateFormat = dateFormat.toLowerCase()
//         }
//         if (this.input.el) {
//             this.props.update(this.input.el.value.replace(DomainSelectorTextField, ''));
//             console.log('this', dateFormat)
//             $(this.input.el).datepicker({
//                 multidate: true,
//                 format: dateFormat,
//             }).trigger('focus');
//         }
//     }
// }
// registry.category("fields").add("multiple_datepicker", DomainSelectorTextField);



// var fieldRegistry = require('web.field_registry');


// const FieldChar = fieldRegistry.get('char');
// // add widget in fieldRegistry with description and without desciption
// fieldRegistry.add('widgetWithDescription', FieldChar.extend({
//     description: "Test Widget",
// }));
// fieldRegistry.add('widgetWithoutDescription', FieldChar.extend({}));




// odoo.define('l10n_do_accounting.l10n_do_accounting', function(require) {
//     "use strict";

//     var basicFields = require('web.basic_fields');
//     var field_registry = require('web.field_registry');

//     var FieldChar = field_registry.get('char');

//     var FieldDgiiAutoComplete = FieldChar.extend({
//         _prepareInput: function($input) {
//             this._super.apply(this, arguments);

//             $input.autocomplete({
//                 source: "/dgii_ws/",
//                 minLength: 3,
//                 select: function(event, ui) {
//                     debugger;
//                     var $rnc = $("input[name$='vat']");

//                     $input.val(ui.item.name);
//                     $rnc.val(ui.item.rnc).trigger("change");


//                     return false;
//                 },
//             });
//         },
//     });

//     field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);

//     return {
//         FieldDgiiAutoComplete: FieldDgiiAutoComplete,
//     };

// });