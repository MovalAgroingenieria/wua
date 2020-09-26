# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Module to monitoring pressurized "
            "irrigation",
    "summary": "In a water users association, added functionality to manage "
               "and compare estimated irrigation needs with real ones",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest", ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_monitoring_config_settings_data.xml",
        "wizard/wizard_generate_controlperiods_view.xml",
        "views/resources.xml",
        "views/base_wua_pressurized_irrigation_monitoring_menus.xml",
        "views/wua_monitoring_config_settings_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_controlperiod_view.xml",
        "views/wua_controlreading_view.xml",
        "views/wua_controlpresconsumption_view.xml",
        "views/wua_negative_controlreading_view.xml",
        "views/wua_comparative_subparcel_presconsumption_view.xml",
        "views/wua_comparative_parcel_presconsumption_view.xml",
        "views/wua_comparative_cultivation_presconsumption_view.xml",
        "views/wua_comparative_partner_presconsumption_view.xml",
        "views/res_partner_view.xml",
        "views/wua_cultivation_view.xml",
        "views/wua_cultivation_kc_view.xml",
        ],
    'qweb': ['static/src/xml/button_import_controlreadings.xml'],
    "installable": True,
    "application": False,
}
