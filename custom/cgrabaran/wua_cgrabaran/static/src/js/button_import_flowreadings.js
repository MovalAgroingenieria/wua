odoo.define('wua_cgrabaran.button_import_flowreadings', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');
var core = require('web.core');

ListView.include({
    render_buttons: function() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            var btn = this.$buttons.find('.button_import_flowreadings');
            btn.on('click', this.proxy('do_button_import_flowreadings'));
        }
    },
    do_button_import_flowreadings: function() {
        var _t = core._t;
        var message = _t('Import flowreadings?')
        var confirmed = confirm(message);
        if (confirmed)
        {
          //alert('Test');
          var python_function = new Model('wua.flowreading').
                                  call("do_import_flowreadings",[]);
            python_function.done(function(result) {
                var title_number_of_flowreadings = _t('Number of flowreadings');
                var title_error_message = _t('WARNING');
                var number_of_flowreadings = result[1];
                var number_of_negative_flowreadings = result[4];
                var suffix_negative_flowreadings = _t('negative readings')
                var error_message = result[2];
                var result_message = title_number_of_flowreadings + ': ' +
                                     number_of_flowreadings.toString();
                if (number_of_negative_flowreadings > 0) {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     number_of_negative_flowreadings.toString() +
                                     ' ' + suffix_negative_flowreadings;
                }
                if (error_message != '') {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     error_message;
                }
                window.alert(result_message);
                if (number_of_flowreadings > 0) {
                    window.location.reload(false);
                }
            });
        }
    }
});

})
