.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================================================================
Separate invoicing of water connections with their own payment method
=====================================================================

For invoice sets of water users associations, this module allows you
to configure any water connection with your own payment method, and send this
water connection to a separate invoice.

Description
===========

It is possible to assign a payment method to a water connection for
invoicing this water connection separately (an invoice for the water
connection).

The payment method can be mapped to water costs or other costs of the
water connection. For water costs, a single partner is allowed with all
the water costs for all parcels of that water connection. Similarly, for
other costs, only one partner is allowed with all costs other than the costs
of water (for all parcels of that water connection).

The separate invoicing for water costs is only possible if the product
category is 10. For separate invoicing for other costs, the category number
is 5.

If there is a previous separate invoicing for parcels, the invoicing separate
for water connections prevails over separate invoicing for parcels.

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

Maintainer
----------

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
