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

1. **Locate the Flow Dashboard**
   After deploying the module, you will find **Flow Dashboard** under
   Dashboards > Grafana > Dashboards.

2. **Import the Dashboard**
   Import the provided JSON file into your Grafana instance.

   .. note::
      You may customize the JSON file to match your organization’s conventions
      before importing.
      The API key has to be configured before importing the dashboard.

3. **Configure the Dashboard Parameter**
   Go to Infrastructure > Configuration > Parameters and choose
   Flow Dashboard from the Grafana Flow section.

4. **View and Adjust**
   The dashboard is now accessible under the **Graph** tab. To change the refresh
   interval, time range, or layout, simply update these settings within Grafana.

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

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
