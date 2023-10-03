# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Management: GIS functions",
    "summary": "In a water users association, management of GIS "
               "entities (with irrigation infrastructure)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
        "base_wua_gis", ],
    "data": [
        "views/wua_irrigationshed_view.xml",
        "views/wua_flowdivider_view.xml",
        "views/wua_airvalve_view.xml",
        "views/wua_valve_view.xml",
        "views/wua_drainagevalve_view.xml",
        "views/wua_irrigationditch_view.xml",
        "views/wua_waterconnection_view.xml"],
    "installable": True,
    "application": False,
}
