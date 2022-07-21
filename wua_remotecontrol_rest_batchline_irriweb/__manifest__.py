# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with BATCHLINE IRRIWEB",
    "summary": "In a water users association, interface of Moval Regadio "
               "with the control remote BATCHLINE IRRIWEB, based on "
               "a REST API",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "base_wua_invoicing", ],
    "data": [
        "data/wua_irrigation_config_settings_data.xml",
        "wizard/wizard_scheduling_waterconnection_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/res_partner_view.xml", ],
    "installable": True,
    "application": False,
}
