.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================================
Water Users Association: Grafana integration for Flow dara graphs
=================================================================

Integration with Grafana of the Moval-Regadío Flow data modules.

Description
===========

This module adds graphics generated in Grafana with the flow data. This allows a
better visualization of the data and an interaction with the generated graph
(zoom to the time frame, annotations, etc.)

Configuration
=============

1.- Upon installing the module, access your Grafana instance and retrieve the
    **Flow Data Dashboard ID**.

2.- Navigate to Infrastructure > Configuration > Parameters and enter the
    Dashboard ID under the **Grafana Flow** section.

3.- The dashboard will appear in the Graph tab using Grafana's default settings.
    To adjust the refresh interval, time range or dashboard layout, simply
   update those parameters within Grafana.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
