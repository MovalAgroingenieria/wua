# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Gravity Irrigation Management for Water Users Associations",
    "summary": "In a water users association, management of the "
               "gravity irrigation",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_structure_irrigation",
        "web_widget_digitized_signature",],
    "data": [
        "security/base_wua_gravity_irrigation_security.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_generate_periods_view.xml",
        "wizard/wizard_copy_requests_view.xml",
        "views/resources.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_wateringperiod_view.xml",
        "views/wua_wateringrequest_view.xml",
        "views/wua_watering_view.xml",
        "views/res_partner_view.xml",
        "views/wua_irrigationditch_view.xml",
        "views/wua_gravconsumption_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_irrigationgate_view.xml",
        "views/hr_views.xml",        
        "reports/wua_wateringrequest_report.xml",],
    "installable": True,
    "application": True,
}
