# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Complaints Channel",
    "summary": "Complaints channel for any water users association.",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "cim_complaints_channel",
    ],
    "data": [
        "data/cim_link_type_data.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "application": False,
}
