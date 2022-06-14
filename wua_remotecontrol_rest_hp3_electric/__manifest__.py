# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with HP3 Electric",
    "summary": "In a water users association, interface of Moval Regadio with "
               "the control remote HP3 Electric, based on a REST API",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "base_wua_remotecontrol_rest_infrastructure", ],
    "data": [
        "data/wua_irrigation_config_settings_data.xml", ],
    "installable": True,
    "application": False,
}
