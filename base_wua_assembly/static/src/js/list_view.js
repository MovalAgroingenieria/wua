odoo.define('base_wua_assembly.ListView.List', function (require) {
"use strict";

var ListView = require('web.ListView');
var core = require('web.core');
var QWeb = core.qweb;

ListView.List.include({
    init: function() {
        this._super.apply(this, arguments);
        if (this.view.model == 'wua.attendance' && this.view.name == 'Attendances') {
            this.options.selectable = false;
        }
    },
});

})