# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing Crop Planning",
    "summary": "In a water users association, invoicing crop "
               "planning for agricultural seasons",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_crop_planning",
     ],
    "data": [
        "data/product_category_data.xml",
        "reports/wua_invoicing_cropplan_report.xml",
        "views/resources.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_cropplan_view.xml",
     ],
    "installable": True,
    "application": False,
}
