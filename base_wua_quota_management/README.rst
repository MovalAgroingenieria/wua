.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================================
Quota Management for various types of irrigation
================================================

Quota management for pressurized irrigation, gravity irrigation and irrigation
based on irrigation reports.

Description
===========

This module adds a quota management to Moval-Regadío. For a set of previously
established periods, an authorized user sets a initial quota of a hydric
superproduct for each partner. With this data, the application processes the
consumptions to update each quota. When a negative value for a quota is
reached, the program informs users and, in certain cases, stops water
consumption.

Functionality:  

* Grouping of water-products in hydric superproducts.
* Management of quota periods.
* Multiple assignment of initial quotas to partners.
* Individual assignment of a bonus to a particular partner.
* Management of cessions.
* Migration of positive balances to the next quota period.
* Operation reports.
* Etc.

Installation
============

You need to install the python bokeh library::

    pip install bokeh==0.12.7

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Miguel Mora <mmora@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
