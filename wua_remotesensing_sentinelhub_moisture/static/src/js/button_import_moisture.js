odoo.define('wua_remotesensing_sentinelhub_moisture.button_import_moisture', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');
var core = require('web.core');

ListView.include({
    render_buttons: function() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            var btn = this.$buttons.find('.button_import_moisture');
            btn.on('click', this.proxy('do_button_import_moisture'));
        }
    },
    do_button_import_moisture: function() {
        var _t = core._t;
        var message = _t('Import all moisture values?')
        var confirmed = confirm(message);
        if (confirmed) {
            var python_function = new Model('wua.parcel').
                                  call("get_all_moisture_values", []);
            python_function.done(function(result) {
                window.location.reload(false);
            });
        }
    }
});

})