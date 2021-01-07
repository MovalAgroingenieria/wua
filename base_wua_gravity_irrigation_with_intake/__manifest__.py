# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Gravity Irrigation Management: With Intake",
    "summary": "In a water users association added link between "
               "irriationditchs and intakes",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_gravity_irrigation",
        "base_wua_infrastructure_primary", ],
    "data": [
        "views/resources.xml",
        "views/wua_gravconsumption_view.xml",
        "views/wua_irrigationditch_view.xml", ],
    "installable": True,
    "application": False,
}
