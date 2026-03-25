# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "WUA Invoicing – Calculate in background (queue)",
    "version": "10.0.1.0.0",
    "category": "Water Users Associations",
    "license": "AGPL-3",
    "summary": "Run invoice set calculation in a queue job and show status via backend_process_status",
    "author": "Moval Agroingeniería",
    "website": "https://www.moval.es",
    "depends": [
        "base_wua_invoicing",
        "queue_job",
        "backend_process_status",
    ],
    "data": [
        "data/queue_channel.xml",
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
}
