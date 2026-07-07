odoo.define('base_wua_invoicing_queue.notification', function (require) {
"use strict";

var WebClient = require('web.WebClient');
var bus = require('bus.bus').bus;

WebClient.include({
    show_application: function () {
        var result = this._super.apply(this, arguments);
        bus.on('notification', this, this._onWuaInvoicesetNotif);
        bus.start_polling();
        return result;
    },

    _onWuaInvoicesetNotif: function (notifications) {
        var self = this;
        for (var i = 0; i < notifications.length; i++) {
            var channel = notifications[i][0];
            var message = notifications[i][1];
            if (channel && channel[0] === 'wua_invoiceset_notif') {
                self.do_notify(message.title, message.message,
                               message.sticky);
            }
        }
    },
});

});
