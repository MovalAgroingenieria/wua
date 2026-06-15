# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "WUA Invoicing – Calculate in background (queue)",
    "version": "10.0.1.2.0",
    "category": "Water Users Associations",
    "license": "AGPL-3",
    "summary": "Run invoice set calculation and parallel validation in "
               "queue jobs, with an on-form progress bar",
    "author": "Moval Agroingeniería",
    "website": "https://www.moval.es",
    "depends": [
        "base_wua_invoicing",
        "queue_job",
    ],
    "data": [
        "security/security.xml",
        "data/queue_channel.xml",
        "data/ir_config_parameter.xml",
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
}
