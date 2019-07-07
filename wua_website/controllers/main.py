# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.http import request

from odoo import http
from odoo.addons.web.controllers.main import Home
from odoo.addons.website.controllers.main import Website


class WuaWebsite(Website):

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        response = Home.web_login(self, redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success']:
            user = request.env['res.users'].browse(request.uid)
            if (user.has_group('base.group_user') or
               user.has_group('base_wua.group_wua_portal_user')):
                redirect = '/web?' + request.httprequest.query_string
            else:
                redirect = '/'
            return http.redirect_with_hash(redirect)
        return response
