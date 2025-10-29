odoo.define('wua_mdm_sensor_management.listview_assign_unassign_device', function (require) {
"use strict";

var ListView = require('web.ListView');
var Model = require('web.DataModel');

ListView.include({
    render_buttons: function() {
        this._super.apply(this, arguments);
        var context = this.dataset && this.dataset.context;
        if (this.$buttons && this.model === 'wua.parcel' && context && context.mapped_device_id) {
            this.$buttons.find('.o_list_button_add').hide();
            this.$buttons.find('.o_button_import').hide();
            var button_assign_device = this.$buttons.find('.button_assign_device');
            var button_unassign_device = this.$buttons.find('.button_unassign_device');
            button_assign_device.on('click', this.proxy('do_button_assign_device'));
            button_unassign_device.on('click', this.proxy('do_button_unassign_device'));
        }
    },
    do_button_assign_device: function() {
        console.log('button_assign_device');
        var selected_ids = this.get_selected_ids();
        var mapped_device_id = this.dataset.context.mapped_device_id;
        var self = this;
        new Model('wua.parcel').call('assign_device_to_parcels', [selected_ids, mapped_device_id]).
            then(function (result) { self.reload(); });
    },
    do_button_unassign_device: function() {
        console.log('button_unassign_device');
        var selected_ids = this.get_selected_ids();
        var mapped_device_id = this.dataset.context.mapped_device_id;
        var self = this;
        new Model('wua.parcel').call('unassign_device_to_parcels', [selected_ids, mapped_device_id]).
            then(function (result) { self.reload(); });
    },
});

})