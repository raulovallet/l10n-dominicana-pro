odoo.define('dgii_report.dgii_report_widget', ['web.field_registry', 'web.basic_fields'], function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var basic_fields = require('web.basic_fields');

    var UrlDgiiReportsWidget = basic_fields.UrlWidget.extend({
        _renderReadonly: function () {
            console.log('UrlDgiiReportsWidget')
            this.$el.text(this.attrs.text || this.value)
                .addClass('o_form_uri o_text_overflow')
                .attr('target', '_blank')
                .attr('href', "dgii_reports/"+this.value);
        },
    });

    field_registry.add('dgii_reports_url', UrlDgiiReportsWidget);

    return {
        UrlDgiiReportsWidget: UrlDgiiReportsWidget,
    };

});