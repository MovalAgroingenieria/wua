.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================================
WUA Invoicing – Calculate in background (queue)
=============================================

This module extends **Water Users Association Invoicing** so that invoice set
calculation and invoice validation can be run in the background via
`queue_job`. It adds buttons that enqueue the calculation and a parallel,
partitioned validation, so the browser does not block. The validation progress
is shown with a progress bar on the invoice-set form.

Usage
=====

* Install this module (this will also install `queue_job` if not already installed).
* Ensure a queue job worker is running for the database (e.g. ``odoo -d yourdb --queue-job-worker`` or your usual way).
* Open an invoice set (WUA → Invoice Sets) in draft, configured and not yet generated.
* Click **Calcular en paralelo** instead of **Calcular**.
* Confirm; the calculation is enqueued and runs in the worker. The form stays open; follow the validation progress bar on the form.

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

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
