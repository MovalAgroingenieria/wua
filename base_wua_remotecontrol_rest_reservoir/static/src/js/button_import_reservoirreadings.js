odoo.define('base_wua_remotecontrol_rest_reservoir.button_import_reservoirreadings', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');
var core = require('web.core');

ListView.include({
    // Get Context of the action
    init: function (parent, action) {
        this.odoo_context = action.context;
        return this._super.apply(this, arguments);
    },
    render_buttons: function() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            var fromShortcut = this.odoo_context &&
                this.odoo_context.from_shortcut;
            var btn = this.$buttons.find('.button_import_reservoirreadings');
            if (fromShortcut) {
                btn.hide();
            } else {
                btn.on('click', this.proxy('do_button_import_reservoirreadings'));
            }
        }
    },
    do_button_import_reservoirreadings: function() {
        var _t = core._t;
        var message = _t('Import reservoir readings?')
        var confirmed = confirm(message);
        if (confirmed) {
            var python_function = new Model('wua.reservoirreading').
                                  call("do_import_reservoirreadings",[]);
            python_function.done(function(result) {
                var title_number_of_reservoirreadings = _t('Number of reservoir readings');
                var title_error_message = _t('WARNING');
                var number_of_reservoirreadings = result[1];
                var error_message = result[2];
                var result_message = title_number_of_reservoirreadings + ': ' +
                                     number_of_reservoirreadings.toString();
                if (error_message != '') {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     error_message;
                }
                window.alert(result_message);
                if (number_of_reservoirreadings > 0) {
                    window.location.reload(false);
                }
            });
        }
    }
});

})
