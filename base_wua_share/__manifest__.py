# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Share management",
    "summary": " In a water users association, \
                 management of share counts",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
    ],
    "data": [
        "views/wua_share_view.xml",
        "views/base_wua_share.xml",
    ],
    "installable": True,
    "application": False,
}
