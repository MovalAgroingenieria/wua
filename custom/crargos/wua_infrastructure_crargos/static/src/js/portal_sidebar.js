odoo.define('wua_infrastructure_crargos.portal_sidebar', function(require) {
"use strict";

var core = require('web.core');
var Sidebar = require('web.Sidebar');
var session = require('web.session');
var Model = require('web.Model');
var Users = new Model('res.users');

var _t = core._t;

Sidebar.include({
    redraw: function() {

      this._super.apply(this, arguments);
      let self = this;
      // Users.call('read', [[session.uid,], ['is_wua_portal_user']]).then(function(user) {
      //   if (user[0].is_wua_portal_user)
      //   {
      //     self.$('.o_dropdown').each(function()
      //     {
      //       let attachments = $(this).find('a');
      //       if (attachments.length > 0)
      //       {
      //         let attachment = attachments[0];
      //         if(attachment.getAttribute('data-section') == 'files')
      //         $(this).hide();
      //       }
      //     });
      //   }
      // })
      // Hides Sidebar sections when portal user
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
    },
});

});
