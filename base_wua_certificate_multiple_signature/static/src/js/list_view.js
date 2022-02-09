odoo.define('base_wua_certificate_multiple_signature.ListView.List', function (require) {
"use strict";

var ListView = require('web.ListView');
var core = require('web.core');
var QWeb = core.qweb;

ListView.List.include({
    render: function() {
        if (this.view.model == 'wua.certificate.user') {
            var self = this;
            this.$current.html(
                QWeb.render('ListView.rows', _.extend({}, this, {
                        render_cell: function () {
                            return self.render_cell.apply(self, arguments); }
                    })));
            this.pad_table_to(1);
        }
        else {
            this._super.apply(this, arguments);
        }
    },
});

})