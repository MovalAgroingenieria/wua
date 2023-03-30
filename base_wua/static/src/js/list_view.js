odoo.define('base_wua.ListView', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var _t = core._t;
    var list_view = require('web.ListView');

    list_view.include({
        render_sidebar: function($node) {
            if (!this.sidebar && this.options.sidebar) {
                this.sidebar = new Sidebar(this, {editable: this.is_action_enabled('edit')});
                if (this.fields_view.toolbar) {
                    this.sidebar.add_toolbar(this.fields_view.toolbar);
                }
                this.sidebar.add_items('other', _.compact([
                    // Make always true to ensure of you can read you can export
                    true && { label: _t("Export"), callback: this.on_sidebar_export },
                    this.is_action_enabled('delete') && this.fields_view.fields.active && {label: _t("Archive"), callback: this.do_archive_selected},
                    this.is_action_enabled('delete') && this.fields_view.fields.active && {label: _t("Unarchive"), callback: this.do_unarchive_selected},
                    this.is_action_enabled('delete') && { label: _t('Delete'), callback: this.do_delete_selected }
                ]));

                $node = $node || this.options.$sidebar;
                this.sidebar.appendTo($node);

                // Hide the sidebar by default (it will be shown as soon as a record is selected)
                this.sidebar.do_hide();
            }
        },
    });

})