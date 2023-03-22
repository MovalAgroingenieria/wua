odoo.define('base_wua_assembly.ListView.List', function (require) {
"use strict";

var ListView = require('web.ListView');
var core = require('web.core');
var QWeb = core.qweb;

ListView.List.include({
    init: function() {
        this._super.apply(this, arguments);
        if (this.view.model == 'wua.attendance' && this.view.fields_view.arch.attrs.class == 'o_base_wua_assembly_attendance_view_tree') {
            this.options.selectable = false;
        }
    },
});

})