# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of pressure consumptions "
            "based on ranges",
    "summary": "In a water users association with pressurized irrigation, "
               "invoicing based on consumption ranges",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_pressurized_irrigation",],
    "data": [
        "security/security.xml",
        "views/wua_invoiceset_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_irrigation_config_settings_view.xml",],
    "installable": True,
    "application": True,
}
