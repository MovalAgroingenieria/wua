# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Crop Planning",
    "summary": "In a water users association, crop planning for "
               "agricultural seasons",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_pressurized_irrigation",
        "web_widget_digitized_signature", ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_subparceltype_data.xml",
        "data/wua_sequences.xml",
        "views/resources.xml",
        "views/wua_cultivation_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_subparceltype_view.xml",
        "views/wua_cropplan_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/res_partner_view.xml",
        "reports/wua_cropplan_report.xml", ],
    "installable": True,
    "application": True,
}
