odoo.define('base_wua.Menu', function (require) {
    "use strict";

    var Menu = require('web.Menu');
    var DataModel = require('web.DataModel');

    Menu.include({
        start: function() {
            this._super.apply(this, arguments);
            const self = this;
            // Modify the href attribute
            const menu_model = new DataModel('ir.ui.menu');
                menu_model.call('search', [[['name', '=', 'GIS Viewer']]], {limit: 1}).then(function(menu_ids) {
                    if (menu_ids.length > 0) {
                        const menu_id = menu_ids[0];
                        const new_href = '/gisviewer';
                        const gis_menus = window.$(`a[data-menu="${menu_id}"]`);
                        gis_menus.attr('href', new_href);
                        gis_menus.attr('target', '_blank');
                    }
            });
        },
    });

})