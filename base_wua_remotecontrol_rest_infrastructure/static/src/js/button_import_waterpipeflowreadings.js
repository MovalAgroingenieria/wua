odoo.define('base_wua_remotecontrol_rest_infrastructure.button_import_waterpipeflowreadings', function (require) {
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
            // Check if comes from other model shortcut  and in that case
            // don't show button, because confuses (All readings)
            var fromShortcut = this.odoo_context &&
                this.odoo_context.from_shortcut;
            var btn = this.$buttons.find('.button_import_waterpipeflowreadings');
            if (fromShortcut) {
                btn.hide();
            } else {
                btn.on('click', this.proxy('do_button_import_waterpipeflowreadings'));
            }
        }
    },
    do_button_import_waterpipeflowreadings: function() {
        var _t = core._t;
        var message = _t('Import water-pipe readings?')
        var confirmed = confirm(message);
        if (confirmed) {
            var python_function = new Model('wua.waterpipeflowreading').
                                  call("do_import_waterpipeflowreadings",[]);
            python_function.done(function(result) {
                var title_number_of_waterpipeflowreadings = _t('Number of water-pipe readings');
                var title_error_message = _t('WARNING');
                var number_of_waterpipeflowreadings = result[1];
                var number_of_negative_waterpipeflowreadings = result[4];
                var suffix_negative_waterpipeflowreadings = _t('negative water-pipe readings')
                var error_message = result[2];
                var result_message = title_number_of_waterpipeflowreadings + ': ' +
                                     number_of_waterpipeflowreadings.toString();
                if (number_of_negative_waterpipeflowreadings > 0) {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     number_of_negative_waterpipeflowreadings.toString() +
                                     ' ' + suffix_negative_waterpipeflowreadings;
                }
                if (error_message != '') {
                    result_message = result_message + '\n\n' +
                                     title_error_message + ': ' +
                                     error_message;
                }
                window.alert(result_message);
                if (number_of_waterpipeflowreadings > 0) {
                    window.location.reload(false);
                }
            });
        }
    }
});

})
