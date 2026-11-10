.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================================
Management of sensor readings grafana
=====================================

Management of sensor readings for measurement devices.

Description
===========

A new portal section is created to allow users to view the sensor readings associated with their measurement devices graphically whith grafana.

Automatic login
===============

The dashboard is loaded in an iframe through ``/my/sensorreadings/grafana``,
which signs the portal user in to Grafana with the shared Grafana user of
``board_grafana_integration`` (see its *Automatic login (JWT)* section), so
the anonymous access of Grafana is not needed.

The path of the dashboard, including the partner and the types of sensor it
filters by, is built on the server from the session of the portal user: the
browser only chooses the view (line or bar chart).

.. warning::

   The portal user gets a Grafana token with the Viewer role, so they can
   query the data sources of that Grafana organization through its API.
   Keep the data source user read-only and restricted to the tables the
   dashboards need.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* Juan José Bautista <jjbautista@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Pablo García <pgarcia@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* José Javier Méndez <jjmendez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
