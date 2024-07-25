odoo.define('custom_user_menu_link.custom_user_menu', function (require) {
    "use strict";

    var UserMenu = require('web.UserMenu');
    var core = require('web.core');
    var QWeb = core.qweb;

    UserMenu.include({
        on_menu_login_cayc: function (event) {
            window.open('https://gestion.cayc.es/web/login', '_blank');
        },
    });
});
