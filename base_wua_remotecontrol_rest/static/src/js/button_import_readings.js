odoo.define('base_wua_remotecontrol_rest.button_import_readings', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');
var core = require('web.core');

ListView.include({
    render_buttons: function() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            var btn = this.$buttons.find('.button_import_readings');
            btn.on('click', this.proxy('do_button_import_readings'));
        }
    },
    do_button_import_readings: function() {
        var _t = core._t;
        var message = _t('Import readings?')
        var confirmed = confirm(message);
        if (confirmed) {
            var python_function = new Model('wua.reading').
                                  call("do_import_readings",[[]]);
            python_function.done(function(result) {
                window.location.reload(false);
            });
        }
    }
});

})