odoo.define('base_wua_portal_user_display.sidebar', function(require) {
"use strict";

var core = require('web.core');
var Sidebar = require('web.Sidebar');
var session = require('web.session');
var Model = require('web.DataModel');

var _t = core._t;

Sidebar.include({
    redraw: function() {

      this._super.apply(this, arguments);
      let self = this;
      var showAttachments;

      var python_function = new Model('ir.values').call(
        'get_default', ['base.config.settings', 'attachments']);
      python_function.done(function(result) {
        showAttachments = result;
        if(! showAttachments)
        {
          session.user_has_group('base_wua.group_wua_portal_user').then(function(has_group)
          {
            if(has_group)
            {
              self.$('.o_dropdown').each(function()
              {
                let attachments = $(this).find('a');
                if (attachments.length > 0)
                {
                  let attachment = attachments[0];
                  if(attachment.getAttribute('data-section') == 'files')
                  {
                    $(this).hide();
                    // Remove because display= none easily restored by user
                    for (let i = 0; i < attachments.length; i++ )
                    {
                      attachments[i].parentElement.remove()
                    }
                  }
                }
              });
            }
          });
        }
      });
    },
});

});
