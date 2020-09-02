odoo.define('base_wua_pressurized_irrigation_monitoring.button_import_controlreadings', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');
var core = require('web.core');

ListView.include({
    render_buttons: function() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            var btn = this.$buttons.find('.button_import_controlreadings');
            btn.on('click', this.proxy('do_button_import_controlreadings'));
        }
    },
    do_button_import_readings: function() {
        var _t = core._t;
        var message = _t('Import readings?')
        var confirmed = confirm(message);
        if (confirmed) {
            var python_function = new Model('wua.controlreading').
                                  call("do_import_controlreadings",[]);
            python_function.done(function(result) {
                var title_number_of_readings = _t('Number of readings');
                var title_error_message = _t('WARNING');
                var number_of_readings = result[1];
                var number_of_negative_readings = result[4];
                var suffix_negative_readings = _t('negative readings')
                var error_message = result[2];
                var result_message = title_number_of_readings + ': ' +
                                     number_of_readings.toString();
                if (number_of_negative_readings > 0) {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     number_of_negative_readings.toString() +
                                     ' ' + suffix_negative_readings;
                }
                if (error_message != '') {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     error_message;
                }
                window.alert(result_message);
                if (number_of_readings > 0) {
                    window.location.reload(false);
                }
            });
        }
    }
});

})
