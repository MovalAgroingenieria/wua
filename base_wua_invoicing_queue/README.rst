.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================================
WUA Invoicing – Calculate in background (queue)
=============================================

This module extends **Water Users Association Invoicing** so that invoice set
calculation can be run in the background via `queue_job`. It adds a button
**Calcular en paralelo** (Calculate in parallel) that enqueues the same
calculation as **Calcular** (Calculate) to a queue job, so the browser does
not block. It also depends on **backend_process_status**, so a green blinking
indicator in the top bar shows when the calculation is running or enqueued.

Usage
=====

* Install this module (this will also install `queue_job` and `backend_process_status` if not already installed).
* Ensure a queue job worker is running for the database (e.g. ``odoo -d yourdb --queue-job-worker`` or your usual way).
* Open an invoice set (WUA → Invoice Sets) in draft, configured and not yet generated.
* Click **Calcular en paralelo** instead of **Calcular**.
* Confirm; the calculation is enqueued and runs in the worker. The form stays open; you can follow the status via the indicator in the top bar.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Miguel Mora <mmora@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Jorge Vera <jvera@moval.es>
 * César Andrés Sanchez <candres@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
